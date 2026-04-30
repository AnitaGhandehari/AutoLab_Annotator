"""
Lightweight Flask server that serves the annotator UI and streams local video files.
Run:  python server.py
Then open http://localhost:5050 in your browser.

Per-video segment boundaries are read from an Excel file next to each video
(same base name, .xlsx), e.g. electrophoresis_1.mp4 → electrophoresis_1.xlsx.
"""

import json
import math
import re
from pathlib import Path

import pandas as pd
from flask import Flask, Response, abort, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")

VIDEOS = {
    "electrophoresis_1": Path(
        r"F:\Anita CV\Internship2026\6) Genetech\Project\Datasets"
        r"\BioVL-QR\BioVL-QR_zip\videos\electrophoresis\Resized\electrophoresis_1.mp4"
    ),
    "extractdna_1": Path(
        r"F:\Anita CV\Internship2026\6) Genetech\Project\Datasets"
        r"\BioVL-QR\BioVL-QR_zip\videos\extractdna\Resized\extractdna_1.mp4"
    ),
}

ANNOTATIONS_DIR = Path(__file__).parent / "annotations"
ANNOTATIONS_DIR.mkdir(exist_ok=True)


def _annotations_path(video_id: str) -> Path:
    return ANNOTATIONS_DIR / f"{video_id}.json"


def _resolve_video(video_id: str) -> Path:
    path = VIDEOS.get(video_id)
    if path is None or not path.exists():
        abort(404, description=f"Unknown video: {video_id}")
    return path


def _norm_key(name: str) -> str:
    return re.sub(r"\s+", "_", str(name).strip().lower())


def _parse_time_to_seconds(val) -> float | None:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    s = str(val).strip()
    if not s:
        return None
    if ":" in s:
        parts = [float(p) for p in s.replace(",", ".").split(":")]
        if len(parts) == 2:
            m, sec = parts
            return m * 60.0 + sec
        if len(parts) == 3:
            h, m, sec = parts
            return h * 3600.0 + m * 60.0 + sec
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def _pick_column(keys: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for c in candidates:
        k = _norm_key(c)
        if k in keys:
            return keys[k]
    return None


def load_segments_from_excel(video_path: Path) -> tuple[list[dict], str | None]:
    """
    Returns (segments, error_message). segments is empty if file missing or unusable.
    Each segment: { idx, start, end, label? }
    """
    xlsx = video_path.with_suffix(".xlsx")
    if not xlsx.exists():
        return [], f"No segment sheet: {xlsx.name}"

    try:
        df = pd.read_excel(xlsx, engine="openpyxl")
    except Exception as e:
        return [], f"Could not read {xlsx.name}: {e}"

    if df.empty or len(df.columns) < 2:
        return [], f"{xlsx.name}: need at least 2 columns (start and end times)"

    col_by_key = {_norm_key(c): c for c in df.columns}
    start_col = _pick_column(
        col_by_key,
        (
            "start",
            "start_sec",
            "start_time",
            "t_start",
            "time_start",
            "begin",
            "from",
            "start_(s)",
            "start_s",
        ),
    )
    end_col = _pick_column(
        col_by_key,
        (
            "end",
            "end_sec",
            "end_time",
            "t_end",
            "time_end",
            "stop",
            "to",
            "end_(s)",
            "end_s",
        ),
    )
    if not start_col or not end_col:
        cols = list(df.columns)
        return (
            [],
            f"{xlsx.name}: could not find start/end columns. Found: {cols}",
        )

    label_col = _pick_column(
        col_by_key,
        ("step", "label", "name", "phase", "description", "procedure", "activity"),
    )

    rows: list[tuple[float, float, str | None]] = []
    for _, row in df.iterrows():
        start = _parse_time_to_seconds(row[start_col])
        end = _parse_time_to_seconds(row[end_col])
        if start is None or end is None:
            continue
        if end < start:
            start, end = end, start
        label = None
        if label_col is not None:
            raw = row[label_col]
            if raw is not None and not (isinstance(raw, float) and math.isnan(raw)):
                label = str(raw).strip() or None
        rows.append((start, end, label))

    if not rows:
        return [], f"{xlsx.name}: no rows with valid start/end times"

    rows.sort(key=lambda r: r[0])
    segments = [
        {"idx": i, "start": s, "end": e, **({"label": lab} if lab else {})}
        for i, (s, e, lab) in enumerate(rows)
    ]
    return segments, None


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/videos")
def list_videos():
    """Return available videos so the frontend can build a selector."""
    return jsonify([
        {"id": vid_id, "label": vid_id.replace("_", " ").title()}
        for vid_id in VIDEOS
        if VIDEOS[vid_id].exists()
    ])


@app.route("/segments/<video_id>")
def get_segments(video_id):
    """Segment time ranges from an .xlsx next to the video (same base name)."""
    video_path = _resolve_video(video_id)
    segs, err = load_segments_from_excel(video_path)
    sheet = video_path.with_suffix(".xlsx")
    return jsonify(
        {
            "video_id": video_id,
            "sheet": sheet.name if sheet.exists() else None,
            "mode": "excel" if segs else "default",
            "segments": segs,
            "error": err,
        }
    )


@app.route("/video/<video_id>")
def stream_video(video_id):
    """Supports HTTP range requests so the browser can seek freely."""
    video_path = _resolve_video(video_id)
    file_size = video_path.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else file_size - 1
        length = end - start + 1

        def generate():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(8192, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return Response(
            generate(),
            status=206,
            mimetype="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
            },
        )

    def generate_full():
        with open(video_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return Response(
        generate_full(),
        status=200,
        mimetype="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        },
    )


@app.route("/annotations/<video_id>", methods=["GET"])
def get_annotations(video_id):
    path = _annotations_path(video_id)
    if path.exists():
        return jsonify(json.loads(path.read_text(encoding="utf-8")))
    return jsonify({})


@app.route("/annotations/<video_id>", methods=["POST"])
def save_annotations(video_id):
    data = request.get_json(force=True)
    path = _annotations_path(video_id)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"status": "saved"})


if __name__ == "__main__":
    missing = [vid for vid, p in VIDEOS.items() if not p.exists()]
    if missing:
        print(f"WARNING: Videos not found: {', '.join(missing)}")
    available = [vid for vid, p in VIDEOS.items() if p.exists()]
    print(f"Serving {len(available)} video(s): {', '.join(available)}")
    print("Open http://localhost:5050 in your browser")
    app.run(host="0.0.0.0", port=5050, debug=False)

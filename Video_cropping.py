import os
import subprocess
import imageio_ffmpeg

"""
Resize BioVL-QR source MP4s for the web annotator: 1280x720, ~15 fps, H.264, no audio.
Outputs go to each video's Resized/ folder. Copy the .mp4 + matching protocols CSV into
video_annotator_web/videos/ (same basename as the app expects).
"""

BASE = r"F:\Anita CV\Internship2026\6) Genetech\Project\Datasets\BioVL-QR\BioVL-QR_zip"

JOBS = [
    {
        "input_path": os.path.join(BASE, "videos", "extractdna", "extractdna_1.mp4"),
        "output_dir": os.path.join(BASE, "videos", "extractdna", "Resized"),
        "output_name": "extractdna_1.mp4",
    },
    {
        "input_path": os.path.join(BASE, "videos", "gel", "gel_1.mp4"),
        "output_dir": os.path.join(BASE, "videos", "gel", "Resized"),
        "output_name": "gel_1.mp4",
    },
]

TARGET_WIDTH = 1280
TARGET_HEIGHT = 720

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()


def run_one(input_path: str, output_path: str) -> None:
    print(f"Input  : {input_path}")
    print(f"Output : {output_path}")
    print(f"Resize to {TARGET_WIDTH}x{TARGET_HEIGHT}, 15 fps, H.264 encoding")
    print("Running ffmpeg (this may take a few minutes)...\n")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        input_path,
        "-vf",
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}",
        "-r",
        "15",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "28",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("ffmpeg FAILED:\n")
        print(result.stderr)
        raise SystemExit(1)

    input_size = os.path.getsize(input_path) / (1024**3)
    output_size = os.path.getsize(output_path) / (1024**3)
    print("Done!")
    print(f"Input  size: {input_size:.2f} GB")
    print(f"Output size: {output_size:.2f} GB ({output_size * 1024:.0f} MB)")
    if input_size > 0:
        print(f"Reduction  : {(1 - output_size / input_size) * 100:.1f}%")
    print()


def main() -> None:
    for job in JOBS:
        inp = job["input_path"]
        out_dir = job["output_dir"]
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, job["output_name"])
        if not os.path.isfile(inp):
            print(f"SKIP (missing input): {inp}\n")
            continue
        run_one(inp, out)


if __name__ == "__main__":
    main()

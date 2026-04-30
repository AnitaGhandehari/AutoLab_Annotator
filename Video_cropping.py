import os
import subprocess
import imageio_ffmpeg

input_path = r"F:\Anita CV\Internship2026\6) Genetech\Project\Datasets\BioVL-QR\BioVL-QR_zip\videos\extractdna\extractdna_1.mp4"
output_dir = r"F:\Anita CV\Internship2026\6) Genetech\Project\Datasets\BioVL-QR\BioVL-QR_zip\videos\extractdna\Resized"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "extractdna_1.mp4")

TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
FPS_DIVISOR = 2

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

print(f"Input  : {input_path}")
print(f"Output : {output_path}")
print(f"Resize to {TARGET_WIDTH}x{TARGET_HEIGHT}, halve fps, H.264 encoding")
print("Running ffmpeg (this may take a few minutes)...\n")

cmd = [
    ffmpeg_exe, "-y",
    "-i", input_path,
    "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}",
    "-r", "15",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "28",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    "-an",
    output_path,
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    print("ffmpeg FAILED:\n")
    print(result.stderr)
    raise SystemExit(1)

input_size = os.path.getsize(input_path) / (1024 ** 3)
output_size = os.path.getsize(output_path) / (1024 ** 3)
print(f"Done!")
print(f"Input  size: {input_size:.2f} GB")
print(f"Output size: {output_size:.2f} GB ({output_size * 1024:.0f} MB)")
print(f"Reduction  : {(1 - output_size / input_size) * 100:.1f}%")

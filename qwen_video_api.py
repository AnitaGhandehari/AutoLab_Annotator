import base64
import mimetypes
import os

from openai import OpenAI


# Set this in PowerShell before running:
# $env:DASHSCOPE_API_KEY="your_api_key_here"
VIDEO_PATH = r"F:\path\to\your\video.mp4"
PROMPT = "Describe this video in detail."
MODEL = "qwen3.5-omni-plus"


def file_to_data_url(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "video/mp4"

    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def main() -> None:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing DASHSCOPE_API_KEY. Set it in PowerShell before running."
        )

    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"Video file not found: {VIDEO_PATH}")

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        # If needed for China region, use:
        # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    video_data_url = file_to_data_url(VIDEO_PATH)

    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": video_data_url,
                        },
                    },
                    {
                        "type": "text",
                        "text": PROMPT,
                    },
                ],
            }
        ],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta:
            text = chunk.choices[0].delta.content
            if text:
                print(text, end="", flush=True)

    print()


if __name__ == "__main__":
    main()

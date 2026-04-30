import os

import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info


VIDEO_PATH = r"F:\Anita CV\Internship2026\6) Genetech\Project\Datasets\BioVL-QR\BioVL-QR_zip\videos\electrophoresis\Resized\electrophoresis_1.mp4"
PROMPT = "Describe this video in detail."

MODEL = "Qwen/Qwen2.5-VL-3B-Instruct"


def main() -> None:
    if not os.path.exists(VIDEO_PATH):
        raise FileNotFoundError(f"Video file not found: {VIDEO_PATH}")

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA not available. Install the CUDA build of PyTorch:\n"
            "  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124"
        )

    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB VRAM)")
    print(f"Loading model {MODEL} in 4-bit ...")

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL,
        quantization_config=quant_config,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(MODEL)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "video",
                    "video": VIDEO_PATH,
                    "max_pixels": 256 * 256,
                    "fps": 0.5,
                },
                {
                    "type": "text",
                    "text": PROMPT,
                },
            ],
        }
    ]

    text_input = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text_input],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    print("Generating response ...")
    generated_ids = model.generate(**inputs, max_new_tokens=512)

    trimmed = [
        out[len(inp) :]
        for inp, out in zip(inputs.input_ids, generated_ids)
    ]

    output_text = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )

    print(output_text[0])


if __name__ == "__main__":
    main()

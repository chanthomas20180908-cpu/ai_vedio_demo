"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_new_mdl.py
"""

import torch
from diffusers import FluxPipeline
from safetensors.torch import load_file
from PIL import Image
import random


def test_flux_model():
    # 固定随机种子，保证可复现
    generator = torch.manual_seed(42)

    # 设置 prompt
    prompt = (
        "The Death of Ophelia by John Everett Millais, "
        "Pre-Raphaelite painting, Ophelia floating in a river surrounded by flowers, "
        "detailed natural elements, melancholic and tragic atmosphere"
    )

    # 加载 FluxPipeline
    pipe = FluxPipeline.from_pretrained(
        "./data/flux",               # 你本地的模型路径（文件夹）
        torch_dtype=torch.bfloat16,  # 使用 bfloat16 节省显存
        use_safetensors=True
    ).to("cuda")

    # 加载 SRPO 权重
    state_dict = load_file("./srpo/diffusion_pytorch_model.safetensors")
    pipe.transformer.load_state_dict(state_dict)

    # 运行推理
    image = pipe(
        prompt,
        guidance_scale=3.5,       # 提示词强度
        height=1024,              # 输出高度
        width=1024,               # 输出宽度
        num_inference_steps=50,   # 迭代步数，越多画质越好
        max_sequence_length=512,  # 文本最大长度
        generator=generator       # 随机数生成器
    ).images[0]

    # 保存图片
    output_path = f"test_output_{random.randint(1000,9999)}.png"
    image.save(output_path)
    print(f"✅ 图片已生成并保存到: {output_path}")


if __name__ == "__main__":
    test_flux_model()

"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：separate_json.py
"""

import json
from typing import Dict, Any, Tuple


# 模拟类型定义，便于IDE识别
class Args:
    def __init__(self, params: Dict[str, Any]):
        self.params = params


Output = Dict[str, Any]


def separate_json_three_parts(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    将JSON数据拆分为三个部分：
    1. main_json: 除 image_description 和 image_url 之外的部分
    2. desc_json: 仅包含 image_description
    3. url_json: 仅包含 image_url

    Args:
        data: 原始JSON字典

    Returns:
        (main_json, desc_json, url_json)
    """
    main_json = {}
    image_description = ""
    image_url = ""
    # desc_json = {}
    # url_json = {}

    for key, value in data.items():
        if key == "image_description":
            image_description = value
        elif key == "image_url":
            image_url = value
        else:
            main_json[key] = value

    return main_json, image_description, image_url


async def main(args: Args) -> Output:
    """
    主函数：接收JSON数据，拆分为三个部分
    输入参数：
    - input: JSON字符串（单个对象）
    """
    params = args.params
    input_str = params.get('input', '')

    try:
        # 解析输入JSON
        data = json.loads(input_str)

        if not isinstance(data, dict):
            raise ValueError("输入JSON必须是对象（非数组）")

        main_json, image_description, image_url = separate_json_three_parts(data)

        ret: Output = {
            "success": True,
            "message": "成功拆分JSON为三个部分",
            "main_json": main_json,
            "image_description": image_description,
            "image_url": image_url
        }

    except json.JSONDecodeError as e:
        ret: Output = {
            "success": False,
            "message": f"JSON解析失败: {str(e)}"
        }
    except Exception as e:
        ret: Output = {
            "success": False,
            "message": f"处理错误: {str(e)}"
        }

    return ret
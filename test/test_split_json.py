"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_split_json.py
"""

import json
from typing import Dict, Any, Tuple, List


# 模拟类型定义，便于IDE识别
class Args:
    def __init__(self, params: Dict[str, Any]):
        self.params = params


Output = Dict[str, Any]


def separate_json(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    将JSON数据中的ref_image分离出来
    返回两个JSON：主JSON（去除ref_image）和图片JSON（仅包含ref_image和元数据）

    Args:
        data: 原始JSON字典

    Returns:
        (main_json, image_json): 主JSON和图片JSON的元组
    """
    # 创建主JSON副本（去除ref_image）
    main_json = {}
    ref_image = None

    for key, value in data.items():
        if key == "ref_image":
            ref_image = value
        else:
            main_json[key] = value

    # 创建图片JSON（包含ref_image和必要的元数据）
    image_json = {
        "ref_image": ref_image,
        "script_order": data.get("script_order"),
        "script_name": data.get("script_name", "")
    }

    return main_json, image_json


async def main(args: Args) -> Output:
    """
    主函数：接收JSON数据，分离ref_image字段

    输入参数：
    - input: JSON字符串（单个对象或数组）
    - mode: 分离模式，"single" 或 "list"（可选，自动检测）
    """
    params = args.params
    input_str = params.get('input', '')

    try:
        # 解析输入JSON
        data = json.loads(input_str)

        main_json, image_json = separate_json(data)
        ret: Output = {
            "success": True,
            "main_json": main_json,
            "image_json": image_json,
            "message": "成功分离单个JSON对象"
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


# 测试数据
test_input_001 = '''{
  "script_order": 1,
  "script_name": "早晨护肤",
  "script_content": "女性在卧室进行护肤",
  "if_product": true,
  "if_model": false,
  "ref_image": "http://example.com/image1.jpg"
}'''

test_input_002 = '''[
  {
    "script_order": 1,
    "script_name": "早晨护肤",
    "script_content": "女性在卧室进行护肤",
    "if_product": true,
    "if_model": false,
    "ref_image": "http://example.com/image1.jpg"
  },
  {
    "script_order": 2,
    "script_name": "产品展示",
    "script_content": "粉底液旋转展示",
    "if_product": true,
    "if_model": false,
    "ref_image": "http://example.com/image2.jpg"
  },
  {
    "script_order": 3,
    "script_name": "使用演示",
    "script_content": "模特涂抹粉底液",
    "if_product": true,
    "if_model": true,
    "ref_image": "http://example.com/image3.jpg"
  }
]'''

test_input_003 = '''{
  "script_order": 5,
  "script_name": "日常应用",
  "script_content": "在不同场景展示完美妆容",
  "if_product": false,
  "if_model": true,
  "ref_image": "http://example.com/model_scene.jpg"
}'''

# 添加调试入口
if __name__ == "__main__":
    import asyncio

    test_cases = [
        ("test_input_001 (单个JSON)", test_input_001, "single"),
        ("test_input_002 (JSON数组)", test_input_002, "list"),
        ("test_input_003 (单个JSON)", test_input_003, "single"),
    ]

    for test_name, test_input, mode in test_cases:
        print(f"\n{'=' * 80}")
        print(f"测试: {test_name}")
        print(f"{'=' * 80}")

        test_params = {
            "input": test_input,
            "mode": mode
        }
        args = Args(test_params)
        result = asyncio.run(main(args))

        print(f"\n成功: {result.get('success', False)}")
        print(f"处理模式: {result.get('mode', 'N/A')}")
        print(f"处理数量: {result.get('count', 0)}")
        print(f"消息: {result.get('message', '')}")

        if result.get('success'):
            print("\n【主JSON】")
            if result.get('mode') == 'list':
                print(json.dumps(result['main_json'], ensure_ascii=False, indent=2))
            else:
                print(json.dumps(result['main_json'], ensure_ascii=False, indent=2))

            print("\n【图片JSON】")
            if result.get('mode') == 'list':
                print(json.dumps(result['image_json'], ensure_ascii=False, indent=2))
            else:
                print(json.dumps(result['image_json'], ensure_ascii=False, indent=2))
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_002.py
"""

import json
import re
from typing import Dict, Any, Union, List


# 模拟类型定义，便于IDE识别
class Args:
    def __init__(self, params: Dict[str, Any]):
        self.params = params


Output = Dict[str, Any]


def extract_json_from_markdown(text: str) -> str:
    """从markdown代码块中提取JSON内容"""
    # 匹配 ```json ... ``` 代码块（可能包含后续文本）
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def extract_json_before_text(text: str) -> str:
    """
    从文本中提取JSON部分，忽略之后的非JSON文本
    处理形如 ```json...```文本 的情况
    """
    # 先尝试找到markdown代码块
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 如果没有markdown代码块，返回原文本
    return text


def unescape_quotes(text: str) -> str:
    """处理转义的引号（如\\"转为\"）"""
    # 将 \\" 替换为 "
    text = text.replace('\\"', '"')
    # 将 \\\\ 替换为 \\
    text = text.replace('\\\\', '\\')
    return text


def clean_input(raw_input: str) -> str:
    """清理输入字符串"""
    # 移除前后的空格、换行符、\n等
    cleaned = raw_input.strip()

    # 处理literal \n
    cleaned = cleaned.replace('\\n', '')

    # 移除行首和行尾的空白字符
    lines = cleaned.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    cleaned = '\n'.join(lines)

    return cleaned


def try_parse_json(text: str) -> Union[dict, list, None]:
    """尝试解析JSON，支持多种格式"""
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        # 尝试处理转义引号后解析
        unescaped = unescape_quotes(text)
        return json.loads(unescaped)
    except json.JSONDecodeError:
        pass

    try:
        # 尝试从markdown代码块中提取
        extracted = extract_json_from_markdown(text)
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass

    try:
        # 尝试先清理再从markdown提取
        cleaned = clean_input(text)
        extracted = extract_json_from_markdown(cleaned)
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass

    try:
        # 尝试清理后直接解析
        cleaned = clean_input(text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    return None


async def main(args: Args) -> Output:
    params = args.params
    input_str = params.get('input', '')

    try:
        # 尝试多种方式解析JSON
        input_data = try_parse_json(input_str)

        if input_data is None:
            # 解析失败
            ret: Output = {
                "key0": input_str,
                "key1": [],
                "key2": {
                    "key21": "JSON parse failed - unrecognized format"
                },
                "success": False
            }
        else:
            # 解析成功，确保key1是列表
            if not isinstance(input_data, list):
                input_data = [input_data]

            ret: Output = {
                "key0": input_str,
                "key1": input_data,
                "key2": {
                    "key21": "Parsed JSON successfully"
                },
                "success": True
            }
    except Exception as e:
        # 捕获所有异常
        ret: Output = {
            "key0": input_str,
            "key1": [],
            "key2": {
                "key21": f"Error: {str(e)}"
            },
            "success": False
        }

    return ret


test_input_001 = '''
\n{"name": "测试用户", "age": 25, "skills": ["Python", "JavaScript"]}\n
'''

test_input_002 = '''
```json\n{"name": "测试用户", "age": 25, "skills": ["Python", "JavaScript"]}\n```
'''

test_input_003 = '''
```json\n[\n    {\n        \"分镜序号\": 1,\n        \"是否包含人物\": true,\n        \"人物信息\": {\n            \"性别\": \"女性\",\n            \"年龄\": \"年轻\",\n            \"发型\": \"精致的发型\",\n            \"服装\": \"优雅的睡衣或家居服\",\n            \"动作\": \"轻抚脸颊，自信微笑\",\n            \"表情\": \"自信、愉悦\"\n        },\n        \"是否包含商品\": false,\n        \"背景与构图\": {\n            \"环境\": \"优雅的卧室\",\n            \"光线\": \"清晨阳光透过落地窗洒进\",\n            \"镜头风格\": \"柔和、温馨\"\n        },\n        \"prompt\": \"清晨阳光透过落地窗洒进优雅的卧室，一位妆容精致的年轻女性轻抚脸颊，自信微笑，穿着优雅的睡衣或家居服，精致的发型，柔和温馨的光线。\"\n    }\n]\n```
'''

test_input_004 = '''
```json\n[\n    {\n        \\"分镜序号\\": 1,\n        \\"是否包含人物\\": true\n    }\n]\n```
思考过程：实打实的萨达
'''

test_input_005 = '''{"simple": "json"}'''

test_input_006 = '''[1, 2, 3, 4, 5]'''

# 添加调试入口
if __name__ == "__main__":
    import asyncio

    test_cases = [
        ("test_input_001", test_input_001),
        ("test_input_002", test_input_002),
        ("test_input_003", test_input_003),
        ("test_input_004", test_input_004),
        ("test_input_005", test_input_005),
        ("test_input_006", test_input_006),
    ]

    # for test_name, test_input in test_cases:
    #     test_params = {"input": test_input}
    #     args = Args(test_params)
    #     result = asyncio.run(main(args))
    #
    #     print(f"\n{'=' * 60}")
    #     print(f"测试: {test_name}")
    #     print(f"{'=' * 60}")
    #     print(f"成功: {result.get('success', False)}")
    #     print(f"解析的JSON列表长度: {len(result.get('key1', []))}")
    #     if result.get('key1'):
    #         print(f"第一个元素类型: {type(result['key1'][0])}")
    #     print(f"状态: {result['key2']['key21']}")

    # 模拟测试数据
    test_params = {
        "input": test_input_004
    }

    # 创建模拟的args对象
    args = Args(test_params)

    # 运行异步函数
    result = asyncio.run(main(args))

    # 打印结果
    print("调试结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

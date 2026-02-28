"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：parse_json_bak.py
"""


import json
import re
from typing import Dict, Any, Union, List


def extract_json_from_markdown(text: str) -> str:
    """从markdown代码块中提取JSON内容
    支持前后都有其他文本的情况
    """
    # 使用正则表达式找到第一个markdown代码块
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def unescape_quotes(text: str) -> str:
    """处理转义的引号（如\\"转为\"）
    支持多层转义：\\\" -> \" 或 \\\\\\" -> \\\"
    """
    # 处理双转义的情况：\\\\" -> \"
    text = text.replace('\\\\"', '"')

    # 处理单转义的情况：\\" -> "
    text = text.replace('\\"', '"')

    # 处理双反斜杠：\\\\ -> \\（但要避免干扰上面的处理）
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


def try_parse_json(text: str, debug: bool = False) -> Union[dict, list, None]:
    """尝试解析JSON，支持多种格式，可选调试模式"""
    attempts = []

    # 尝试1：直接解析
    try:
        result = json.loads(text)
        if debug:
            print("✓ 尝试1成功：直接解析")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试1失败：{str(e)[:50]}")

    # 尝试2：处理转义引号后解析
    try:
        unescaped = unescape_quotes(text)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试2成功：处理转义引号后解析")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试2失败：{str(e)[:50]}")

    # 尝试3：从markdown代码块中提取
    try:
        extracted = extract_json_from_markdown(text)
        result = json.loads(extracted)
        if debug:
            print("✓ 尝试3成功：从markdown代码块中提取")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试3失败：{str(e)[:50]}")

    # 尝试4：从markdown提取 + 处理转义引号
    try:
        extracted = extract_json_from_markdown(text)
        unescaped = unescape_quotes(extracted)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试4成功：从markdown提取 + 处理转义引号")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试4失败：{str(e)[:50]}")

    # 尝试5：先清理再从markdown提取
    try:
        cleaned = clean_input(text)
        extracted = extract_json_from_markdown(cleaned)
        result = json.loads(extracted)
        if debug:
            print("✓ 尝试5成功：清理后从markdown提取")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试5失败：{str(e)[:50]}")

    # 尝试6：清理 + markdown提取 + 处理转义引号
    try:
        cleaned = clean_input(text)
        extracted = extract_json_from_markdown(cleaned)
        unescaped = unescape_quotes(extracted)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试6成功：清理 + markdown提取 + 处理转义引号")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试6失败：{str(e)[:50]}")

    # 尝试7：清理后直接解析
    try:
        cleaned = clean_input(text)
        result = json.loads(cleaned)
        if debug:
            print("✓ 尝试7成功：清理后直接解析")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试7失败：{str(e)[:50]}")

    # 尝试8：markdown提取 + 多次处理转义引号
    try:
        extracted = extract_json_from_markdown(text)
        unescaped = unescape_quotes(extracted)
        # 再处理一次，处理可能的嵌套转义
        unescaped = unescape_quotes(unescaped)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试8成功：markdown提取 + 多次处理转义引号")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试8失败：{str(e)[:50]}")

    # 尝试9：清理 + markdown提取 + 多次处理转义引号
    try:
        cleaned = clean_input(text)
        extracted = extract_json_from_markdown(cleaned)
        unescaped = unescape_quotes(extracted)
        unescaped = unescape_quotes(unescaped)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试9成功：清理 + markdown提取 + 多次处理转义引号")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试9失败：{str(e)[:50]}")

    if debug:
        print("\n所有尝试失败：")
        for attempt in attempts:
            print(f"  {attempt}")

    return None


async def main(args: Args) -> Output:
    params = args.params
    # input_str = params.get('input', 'test_csy')
    # input_str = params['input']

    try:
        # 尝试多种方式解析JSON
        input_data = try_parse_json(params['input'])

        if input_data is None:
            # 解析失败
            ret: Output = {
                "key0": params['input'],
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
                "key0": params['input'],
                "key1": input_data,
                "key2": {
                    "key21": "Parsed JSON successfully"
                },
                "success": True
            }
    except Exception as e:
        # 捕获所有异常
        ret: Output = {
            "key0": params['input'],
            "key1": [],
            "key2": {
                "key21": f"Error: {str(e)}"
            },
            "success": False
        }

    return ret

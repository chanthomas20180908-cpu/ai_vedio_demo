"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：try_parse_json.py
"""

import json
import re
from typing import Dict, Any, Union, List



def extract_json_from_markdown(text: str) -> str:
    """从markdown代码块中提取JSON内容"""
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def aggressive_unescape(text: str, max_iterations: int = 10) -> str:
    """激进的转义处理 - 移除所有多余的反斜杠

    这个函数处理各种转义情况：
    1. \\" -> "
    2. \\n -> \n (如果在字符串值中)
    3. \\\\ -> \\
    4. 递归处理多层转义（最多max_iterations次）
    """
    original = text
    
    for _ in range(max_iterations):
        # 使用正则表达式找到并替换转义的引号
        # 匹配：多个反斜杠后面跟着引号，只保留一个引号
        text = re.sub(r'\\+"', '"', text)
        
        # 处理反斜杠本身的转义：\\\\ -> \\
        text = text.replace('\\\\', '\\')
        
        # 如果没有变化，说明已经处理完成
        if text == original:
            break
        original = text
    
    # 最后清理：如果还有 \" 直接替换为 "
    text = text.replace('\\"', '"')
    
    return text


def process_literal_newlines(text: str) -> str:
    """处理字符串中的 literal \\n（两个字符：\\ 和 n）
    转换为真正的换行符
    """
    text = text.replace('\\n', '\n')
    text = text.replace('\\r', '\r')
    text = text.replace('\\t', '\t')
    return text


def extract_nested_json(data: Union[dict, list]) -> Union[dict, list]:
    """递归提取嵌套的JSON字符串
    
    处理像 {"image_prompts": "```json\n[...]\n```"} 这样的情况
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # 尝试解析字符串值为JSON
                parsed = try_parse_json(value, debug=False)
                if parsed is not None:
                    result[key] = extract_nested_json(parsed)
                else:
                    result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = extract_nested_json(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [extract_nested_json(item) for item in data]
    else:
        return data


def decode_python_string_literal(text: str) -> str:
    """尝试将文本作为Python字符串字面量解码
    
    处理像 '\\n' 这样的字符串，将其转换为真正的换行符
    """
    try:
        # 尝试将其作为Python字符串字面量解码
        # 注意：这里使用 'unicode_escape' 编码来解码转义序列
        decoded = text.encode('utf-8').decode('unicode_escape')
        return decoded
    except:
        return text


def try_parse_json(text: str, debug: bool = False) -> Union[dict, list, None]:
    """尝试多种方式解析JSON"""
    attempts = []

    # 尝试1：直接解析
    try:
        result = json.loads(text)
        if debug:
            print("✓ 尝试1成功：直接解析")
        # 检查是否需要进一步提取嵌套JSON
        if isinstance(result, dict) and any(isinstance(v, str) and ('```' in v or '[' in v or '{' in v) for v in result.values()):
            nested_result = extract_nested_json(result)
            if nested_result != result:
                if debug:
                    print("  → 检测到嵌套JSON，已递归解析")
                return nested_result
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试1失败：{str(e)[:80]}")

    # 尝试2：markdown提取
    try:
        extracted = extract_json_from_markdown(text)
        result = json.loads(extracted)
        if debug:
            print("✓ 尝试2成功：markdown提取")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试2失败：{str(e)[:80]}")

    # 尝试3：markdown + 激进转义处理
    try:
        extracted = extract_json_from_markdown(text)
        unescaped = aggressive_unescape(extracted)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试3成功：markdown + 激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试3失败：{str(e)[:80]}")

    # 尝试4：literal \\n处理 + markdown
    try:
        processed = process_literal_newlines(text)
        extracted = extract_json_from_markdown(processed)
        result = json.loads(extracted)
        if debug:
            print("✓ 尝试4成功：literal \\n + markdown")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试4失败：{str(e)[:80]}")

    # 尝试5：literal \\n + markdown + 激进转义
    try:
        processed = process_literal_newlines(text)
        extracted = extract_json_from_markdown(processed)
        unescaped = aggressive_unescape(extracted)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试5成功：literal \\n + markdown + 激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试5失败：{str(e)[:80]}")

    # 尝试6：直接激进转义
    try:
        unescaped = aggressive_unescape(text)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试6成功：直接激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试6失败：{str(e)[:80]}")

    # 尝试7：literal \\n + 直接激进转义
    try:
        processed = process_literal_newlines(text)
        unescaped = aggressive_unescape(processed)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试7成功：literal \\n + 直接激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试7失败：{str(e)[:80]}")

    # 尝试8：清理空白 + markdown
    try:
        extracted = extract_json_from_markdown(text)
        cleaned = re.sub(r'\s+', ' ', extracted).strip()
        result = json.loads(cleaned)
        if debug:
            print("✓ 尝试8成功：清理空白 + markdown")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试8失败：{str(e)[:80]}")

    # 尝试9：清理空白 + markdown + 激进转义
    try:
        extracted = extract_json_from_markdown(text)
        cleaned = re.sub(r'\s+', ' ', extracted).strip()
        unescaped = aggressive_unescape(cleaned)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试9成功：清理空白 + markdown + 激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试9失败：{str(e)[:80]}")

    # 尝试10：literal \\n + 清理空白 + markdown + 激进转义
    try:
        processed = process_literal_newlines(text)
        extracted = extract_json_from_markdown(processed)
        cleaned = re.sub(r'\s+', ' ', extracted).strip()
        unescaped = aggressive_unescape(cleaned)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试10成功：literal \\n + 清理空白 + markdown + 激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试10失败：{str(e)[:80]}")

    # 尝试11：Python字符串字面量解码
    try:
        decoded = decode_python_string_literal(text)
        result = json.loads(decoded)
        if debug:
            print("✓ 尝试11成功：Python字符串字面量解码")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试11失败：{str(e)[:80]}")

    # 尝试12：Python字符串字面量解码 + markdown
    try:
        decoded = decode_python_string_literal(text)
        extracted = extract_json_from_markdown(decoded)
        result = json.loads(extracted)
        if debug:
            print("✓ 尝试12成功：Python字符串字面量解码 + markdown")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试12失败：{str(e)[:80]}")

    # 尝试13：Python字符串字面量解码 + markdown + 激进转义
    try:
        decoded = decode_python_string_literal(text)
        extracted = extract_json_from_markdown(decoded)
        unescaped = aggressive_unescape(extracted)
        result = json.loads(unescaped)
        if debug:
            print("✓ 尝试13成功：Python字符串字面量解码 + markdown + 激进转义")
        return result
    except json.JSONDecodeError as e:
        if debug:
            attempts.append(f"✗ 尝试13失败：{str(e)[:80]}")

    if debug:
        print("\n所有尝试失败：")
        for attempt in attempts:
            print(f"  {attempt}")

    return None


# ================================================================================


class Args:
    def __init__(self, params: Dict[str, Any]):
        self.params = params


Output = Dict[str, Any]

# ================================================================================


async def main(args: Args) -> Output:
    params = args.params
    # input_str = params.get('input', '')
    input_str = params['input']


    try:
        # 尝试多种方式解析JSON
        input_data = try_parse_json(input_str)

        if input_data is None:
            # 解析失败
            ret: Output = {
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
                "key1": input_data,
                "key2": {
                    "key21": "Parsed JSON successfully"
                },
                "success": True
            }
    except Exception as e:
        # 捕获所有异常
        ret: Output = {
            "key1": [],
            "key2": {
                "key21": f"Error: {str(e)}"
            },
            "success": False
        }

    return ret

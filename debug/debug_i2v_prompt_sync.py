"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_i2v_prompt_sync.py
"""

import os
import time

from dotenv import load_dotenv

from component.chat.chat import chat_with_model
from config.logging_config import setup_logging, get_logger
from data.prompt.system_prompt import I2V_PROMPT_SYNC_PROMPT

logger = get_logger(__name__)


def debug_i2v_prompt_sync(_api_key, _user_input):

    system_prompt = I2V_PROMPT_SYNC_PROMPT
    res_list = []
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": _user_input,
        }
    ]

    # TODO csy 2-251210:优化代码结构
    model = "qwen-max"
    logger.info(f"使用模型: {model}")
    res = chat_with_model(
        api_key=_api_key,
        messages=messages,
        model_type="qwen",
        model=model,
        extra_body={"enable_thinking": True},
    )
    res_list.append({
        "model": model,
        "res": res,
    })

    model = "qwen-plus"
    logger.info(f"使用模型: {model}")
    res = chat_with_model(
        api_key=_api_key,
        messages=messages,
        model_type="qwen",
        model=model,
        extra_body={"enable_thinking": True},
    )
    res_list.append({
        "model": model,
        "res": res,
    })

    # model = "deepseek-r1"
    # logger.info(f"使用模型: {model}")
    # res = chat_with_model(
    #     api_key=_api_key,
    #     messages=messages,
    #     model_type="deepseek",
    #     model=model,
    #     extra_body={"enable_thinking": True},
    # )
    # res_list.append({
    #     "model": model,
    #     "res": res,
    # })

    model = "deepseek-v3.2"
    logger.info(f"使用模型: {model}")
    res = chat_with_model(
        api_key=_api_key,
        messages=messages,
        model_type="deepseek",
        model=model,
        extra_body={"enable_thinking": True},
    )
    res_list.append({
        "model": model,
        "res": res,
    })

    return res_list


if __name__ == "__main__":
    setup_logging()

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    start_time = time.time()

    user_input = '''
    在受了委屈,或是遇到完全离谱的事情,情绪抒发类(生气,无奈,难过等等)的表情包动图,要夸张,表达情绪
    '''
    res = debug_i2v_prompt_sync(api_key, user_input)  # res 是一个 [ { ... }, ... ] 列表

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(os.path.dirname(__file__), "data/temp")
    os.makedirs(out_dir, exist_ok=True)

    # 直接写入文本文件（字符串化整个列表）
    out_path = os.path.join(out_dir, f"i2v_prompt_res_{timestamp}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(res))  # 或者使用 json.dumps(res, ensure_ascii=False, indent=2)

    for r in res:
        print(f"[{r.get('model')}] response:\n {r.get('res')}")

    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")
    print(f"结果已保存为: {out_path}")

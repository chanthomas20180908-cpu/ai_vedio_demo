"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: Kling API 配置
Output: Kling API 调用接口
Pos: Kling 模型 API 封装层
"""

import os
import time
import jwt
from dotenv import load_dotenv

from config.logging_config import get_logger


logger = get_logger(__name__)


def encode_jwt_token(_ak=None, _sk=None):
    # 如果仍然为空，则尝试从环境变量加载
    if _ak is None or _sk is None:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../env/default.env"))
        _ak = os.getenv("KLING_Access_Key") if _ak is None else _ak
        _sk = os.getenv("KLING_Secret_Key") if _sk is None else _sk

    # 添加参数验证
    if _ak is None or _sk is None:
        raise ValueError("请填写access key和secret key")

    # 设置JWT payload
    current_time = int(time.time())
    exp_time = current_time + 1800  # 30分钟有效期
    nbf_time = current_time - 5     # 5秒前开始生效

    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": _ak,
        "exp": exp_time,   # 有效时间，当前时间+1800s(30min)
        "nbf": nbf_time    # 开始生效的时间，当前时间-5秒
    }

    token = jwt.encode(payload, _sk, headers=headers)

    # 打印API key和有效时间信息
    logger.info(f"kling_api_key刷新成功: {token}")
    logger.info(f"API key有效期: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(nbf_time))} 至 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exp_time))}")

    return token



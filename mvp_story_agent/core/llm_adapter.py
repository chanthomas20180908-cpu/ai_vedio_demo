import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from config.logging_config import get_logger

logger = get_logger(__name__)
from component.chat.chat import chat_with_model


def _prompt_path(role: str) -> Path:
    base = Path(__file__).resolve().parents[1] / "prompts" / "roles"
    md = base / f"{role}.md"
    if md.exists():
        return md
    return base / f"{role}.txt"


def load_prompt(role: str) -> str:
    p = _prompt_path(role)
    if not p.exists():
        raise SystemExit(f"Prompt not found: {p}")
    return p.read_text(encoding="utf-8")


def _default_api_key_env(model_type: str) -> str:
    mt = (model_type or "").lower()
    if mt == "gemini":
        return "GEMINI_API_KEY"
    if mt in ("qwen", "deepseek"):
        return "DASHSCOPE_API_KEY"
    return "GEMINI_API_KEY"


def _resolve_api_key(api_key: Optional[str], env_name: str) -> str:
    if api_key:
        return api_key

    # Keep project convention: try env/default.env first.
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    except Exception:
        pass

    key = os.getenv(env_name)
    if not key:
        raise ValueError(f"未找到 {env_name}，请设置环境变量或在函数参数中传入 api_key")
    return key


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model output")
    try:
        return json.loads(text)
    except Exception:
        pass
    # try to extract first JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        snippet = text[start : end + 1]
        return json.loads(snippet)
    raise ValueError("Failed to parse JSON from model output")


def call_role(
    *,
    role: str,
    payload: Dict[str, Any],
    model_type: str,
    model: str,
    api_key_env: Optional[str] = None,
    thinking_level: Optional[str] = None,
) -> str:
    prompt = load_prompt(role)
    payload_text = json.dumps(payload, ensure_ascii=False)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": payload_text},
    ]

    env_name = api_key_env or _default_api_key_env(model_type)
    api_key = os.getenv(env_name, "")
    api_key = _resolve_api_key(api_key or None, env_name)
    _preview_len = 500
    _preview = payload_text if len(payload_text) <= _preview_len else (payload_text[:_preview_len] + "...<truncated>")
    logger.debug(
        "llm call | role=%s model_type=%s model=%s payload_chars=%s prompt_chars=%s",
        role,
        model_type,
        model,
        len(payload_text),
        len(prompt),
    )
    logger.debug("llm payload preview | role=%s | %s", role, _preview)

    kwargs = {}
    if (model_type or "").lower() == "gemini" and thinking_level:
        kwargs["thinking_level"] = thinking_level

    result = chat_with_model(
        api_key=api_key,
        model_type=model_type,
        model=model,
        messages=messages,
        **kwargs,
    )
    if result is None:
        raise SystemExit("LLM call failed (empty response)")

    _resp_preview = result if len(result) <= _preview_len else (result[:_preview_len] + "...<truncated>")
    logger.debug("llm response | role=%s chars=%s", role, len(result))
    logger.debug("llm response preview | role=%s | %s", role, _resp_preview)
    return result


def call_role_json(**kwargs) -> Dict[str, Any]:
    text = call_role(**kwargs)
    return _extract_json(text)

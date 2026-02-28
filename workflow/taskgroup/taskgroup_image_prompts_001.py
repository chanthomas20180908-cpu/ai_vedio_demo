"""兼容入口（已废弃）。

请改用：workflow/taskgroup/taskgroup_image_prompts_sync_001.py
"""

from __future__ import annotations

from workflow.taskgroup.taskgroup_image_prompts_sync_001 import (  # noqa: F401
    ImagePromptsResult,
    image_prompts_sync_001,
    write_image_prompts_json,
)


def generate_image_prompts_001(*args, **kwargs):  # type: ignore
    raise RuntimeError(
        "generate_image_prompts_001 已废弃，请改用 image_prompts_sync_001(text, system_prompt=..., user_prompt_template=...)"
    )

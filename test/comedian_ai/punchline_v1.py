"""test/comedian_ai/punchline_story.py

Raw-story → multi-step punchline generator.

Use case: feed in一段用户口述文本（无结构），模型分三步：
1. 理解 & 规划结构
2. 根据结构写草稿
3. 严苛编辑输出最终段子
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List

from dotenv import load_dotenv

from component.chat.chat import chat_with_model

try:
    from config.logging_config import get_logger, setup_logging  # type: ignore

    logger = get_logger(__name__)
except Exception:  # pragma: no cover
    logger = None


def _log_info(msg: str) -> None:
    if logger is not None:
        logger.info(msg)


def _log_debug(msg: str) -> None:
    if logger is not None:
        logger.debug(msg)


# ------------------------------
# Prompts (raw story pipeline)
# ------------------------------

# Step A is a 2-step killer: minimal core + alternate angles.

# A1_PREMISE_COMPRESSOR_SYSTEM = """你是单口喜剧“前提压缩器”。目标：从原始口述中提炼能直接写稿的核心。
# 你只输出三个字段：PREMISE / COMEDIC_FLAW / EVIDENCE_PICK。
#
# 硬性规则：
# - 禁止杜撰事实：不得新增原文没有的角色/情节/设定。
# - 禁止写段子正文：不输出完整段子，不写笑点段落。
# - 禁止长篇分析：每个字段都要短、尖、像能上台说。
#
# 输出格式（逐行，禁止遗漏）：
# PREMISE: <1句，尖锐的原创观察，不讲时间线>
# COMEDIC_FLAW: <1句：我哪里好笑/哪里废/哪里不具备获胜技能>
# EVIDENCE_PICK: ["...", "...", "...", "...", "..."]
# """
#
# A1_PREMISE_COMPRESSOR_USER_TMPL = """原始故事（不要改写，只供理解）：
# {raw_story}
#
# 任务：按字段输出。
# """
#
# A2_ALT_ANGLES_SYSTEM = """你是单口喜剧“第二视角发生器”。你的任务不是改写A1，也不是打标签。
# 你的任务是：基于同一段原故事，提出3条完全不同的喜剧解释路径（每条都能直接用于机关/包袱）。
#
# 硬性要求：
# - 三条 ANGLE 必须彼此不同，且至少有一条与A1的视角相反或更残酷。
# - 不得新增事实/角色/剧情；只能在解释角度、荒谬规则、夸张推理上创作。
# - 不写完整段子，只给可用“角度+机制+底句方向”。
#
# 输出格式（严格照抄）：
# ALT_ANGLES:
# - ANGLE_1: <1句新前提>
#   MECHANISM_1: <1句机制/荒谬规则>
#   PUNCHLINE_SEED_1: <1句底句方向>
# - ANGLE_2: <1句新前提>
#   MECHANISM_2: <1句机制/荒谬规则>
#   PUNCHLINE_SEED_2: <1句底句方向>
# - ANGLE_3: <1句新前提>
#   MECHANISM_3: <1句机制/荒谬规则>
#   PUNCHLINE_SEED_3: <1句底句方向>
# """
#
# A2_ALT_ANGLES_USER_TMPL = """A1 输出如下：
# {a1_text}
#
# 原始故事（仅供核对，不要复述）：
# {raw_story}
#
# 任务：按字段输出 A2。
# """

A1_PREMISE_COMPRESSOR_SYSTEM = """你是单口喜剧“前提压缩器”。目标：从原始口述中提炼能直接写稿的核心。
你只输出三个字段：SCENE_SNAPSHOT / COMEDIC_FLAW / PREMISE。

硬性规则：
- 禁止杜撰事实：不得新增原文没有的角色/情节/设定。
- 禁止受害者心态：COMEDIC_FLAW 必须是主角的主观性格缺陷（如：虚荣、强迫症、过度戏精、懦弱），而不仅仅是“倒霉”或“无能”。
- 禁止长篇分析：每个字段都要短、尖、像能上台说。

输出格式（逐行，禁止遗漏）：
SCENE_SNAPSHOT: <1句：用动词+名词描绘最狼狈/最荒诞的那个定格画面>
COMEDIC_FLAW: <1句：主角在这个困境中暴露的可笑性格弱点（不要写客观弱点，要写主观毛病）>
PREMISE: <1句：结合画面与弱点，提炼出的核心观点（格式：我觉得X事简直就是Y / 我发现自己根本不是Z）>
"""

A1_PREMISE_COMPRESSOR_USER_TMPL = """原始故事（不要改写，只供理解）：
{raw_story}

任务：按字段输出。
"""

A2_ALT_ANGLES_SYSTEM = """你是单口喜剧“梗概发散器”。你的任务是基于 A1 的核心，分裂出 3 条完全不同的喜剧解释路径。

你需要提供以下三种特定方向的 ANGLE：
1. 【自嘲视角】：全是“我”的错（我的虚荣/愚蠢/强迫症导致了这一切）。
2. 【阴谋视角】：全是“世界”的错（把环境/物品拟人化，赋予它恶意的荒谬逻辑）。
3. 【行动视角】：为了维持荒谬局面，我做出的更荒谬的适应性行为（Solve）。

硬性要求：
- 不得新增事实/角色/剧情；只能在解释角度、荒谬规则、夸张推理上创作。
- 禁止书面语：输出要像口语，像在舞台上讲。

输出格式（严格照抄）：
ALT_ANGLES:
- ANGLE_TYPE: 自嘲视角
  PREMISE_HOOK: <1句：这个角度的观点句>
  ABSURD_LOGIC: <1句：支撑这个观点的荒谬推论>
  ACT_OUT_IDEA: <1句：如何表演/重现这个场景（动作或独白）>

- ANGLE_TYPE: 阴谋视角
  PREMISE_HOOK: <1句：这个角度的观点句>
  ABSURD_LOGIC: <1句：支撑这个观点的荒谬推论>
  ACT_OUT_IDEA: <1句：如何表演/重现这个场景（动作或独白）>

- ANGLE_TYPE: 行动视角
  PREMISE_HOOK: <1句：这个角度的观点句>
  ABSURD_LOGIC: <1句：支撑这个观点的荒谬推论>
  ACT_OUT_IDEA: <1句：如何表演/重现这个场景（动作或独白）>
"""

A2_ALT_ANGLES_USER_TMPL = """A1 输出如下：
{a1_text}

原始故事（仅供核对，不要复述）：
{raw_story}

任务：按字段输出 A2。
"""


T2_DIMENSION_SYSTEM = """你是单口喜剧结构选择器。
你只做一件事：在四大维度里选 1 个最适合这个材料的维度。
四选一：语言语义 / 叙事节奏 / 认知冲突 / 社会行为。
输出必须包含：
DIMENSION: <四选一>
WHY: <不超过2句，引用材料里的具体点说明为什么>
"""

T2_DIMENSION_USER_TMPL = """材料如下：
{material_text}

任务：选择最适合的 DIMENSION，并给出 WHY。
"""

T3_METHOD_SYSTEM = """你是单口喜剧方法选择器。
你只做一件事：在13种方法里选 1 个最适合这个材料的“方法ID+名称”。
你必须从下列之一选择（照抄ID与名称）：
1.1 语义双关
1.2 简单真相
1.3 配对短语
1.4 自相矛盾（语义类）
2.1 反转
2.2 三步定律
2.3 比较和对比
3.1 制造反差（不协调并置）
3.2 喜剧讽刺
3.3 自相矛盾（逻辑类）
4.1 制造优越感
4.2 观察式喜剧
4.3 绵里藏针
4.4 闹剧
输出格式固定：
METHOD: <ID 名称>
WHY: <不超过2句，引用材料里的具体点说明>
"""

T3_METHOD_USER_TMPL = """材料如下：
{material_text}

维度选择如下：
{dimension_text}

任务：选择 1 个 METHOD，并给出 WHY。
"""

T4_MECHANISM_SYSTEM = """你是单口喜剧“机关”设计师（预期违背）。
你只做一件事：把材料落到机关模板：Story1 → Connector → Story2。
硬性规则：
- 只能使用材料里的 PREMISE/COMEDIC_FLAW/EVIDENCE_PICK/ALT_ANGLES，禁止新增角色/剧情。
- Story1 是观众默认预期（目标假设），一句话。
- Connector 是触发点（词/动作/规则/并置），一句话，要尽量引用 EVIDENCE_PICK 的原话。
- Story2 是再解读/荒谬结论，一句话。
最后把结果整理成可写稿的骨架（字段固定，逐行输出，禁止遗漏）：
PREMISE: <沿用材料的premise，允许轻微打磨但不换意思>
DIMENSION: <沿用>
METHOD: <沿用>
STORY1: <一句话>
CONNECTOR: <一句话>
STORY2: <一句话>
EVIDENCE_PICK: [从材料里挑3-5条，原话优先]
"""

T4_MECHANISM_USER_TMPL = """材料如下：
{material_text}

维度：
{dimension_text}

方法：
{method_text}

任务：设计机关并输出骨架字段。
"""

DRAFT_SYSTEM = """你是单口喜剧草稿写手。任务：根据结构提纲写一条 160-220 字、3-6 句、包袱在末句的段子。
要求：
- 绝不新增剧情或角色，只能使用结构的元素与细节
- 口语化、有画面，可保留1-2处对话
- 禁止网络烂梗/谐音梗/鸡汤
- 包袱（底）必须在最后一句，最后一句之后不要再解释
"""

DRAFT_USER_TMPL = """根据下面的结构写一条段子（直接输出段子文本，不要任何说明）：
{structure_text}
"""

EDIT_SYSTEM = """你是严苛的单口喜剧逐字稿编辑。
你只做减法和锐化：删废话、把节奏收紧、确保底在最后一句。
禁止新增段落、禁止扩写新剧情、禁止换主题。
输出只给最终段子文本，不要任何解释。"""

EDIT_USER_TMPL = """把下面草稿编辑成可上台逐字稿：
硬性要求：
- 只保留1-2处对话
- 总长度 160-220 字
- 最后一句必须是包袱（底在句末），底后不要再解释
- 保持“我”的情绪：暴怒/无奈，但表达要干净利落

中心前提（不可丢）：{core_premise}

草稿：
{draft_text}
"""


# ------------------------------
# Model call stub (reuse deepseek wrapper)
# ------------------------------

def call_model(messages: List[Dict[str, str]], stage_name: str) -> str:
    """Wire this to deepseek-v3.2 via existing chat_with_model helper."""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    try:
        response = chat_with_model(
            api_key=api_key,
            messages=messages,
            model_type="deepseek",
            model="deepseek-v3.2",
            extra_body={"enable_thinking": False},
        )
        _log_debug(f"[{stage_name}] AI 响应长度: {len(response)}")
        return response
    except Exception as exc:  # pragma: no cover
        if logger:
            logger.error(f"[{stage_name}] AI 调用失败: {exc}")
        raise


# ------------------------------
# Helpers
# ------------------------------

def extract_core_premise(structure_text: str, fallback: str = "我发现日常小事背后的荒谬特别好笑。") -> str:
    for line in structure_text.splitlines():
        normalized = line.strip()
        if normalized.upper().startswith("PREMISE"):
            return normalized.split(":", 1)[1].strip() or fallback
    return fallback


def text_stats(text: str) -> Dict[str, int]:
    sentences = [s for s in text.replace("！", "。").replace("？", "。").split("。") if s.strip()]
    dialogs = text.count("“") + text.count('"')
    length = len(text)
    return {"sentences": len(sentences), "dialogs": dialogs, "length": length}


def _print_separator(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# ------------------------------
# Result & pipeline
# ------------------------------

@dataclass
class PunchlineResult:
    raw_story: str
    structure_text: str
    draft_text: str
    final_text: str
    draft_stats: Dict[str, int]
    final_stats: Dict[str, int]


def generate_punchline_from_story(raw_story_text: str) -> PunchlineResult:
    if not raw_story_text.strip():
        raise ValueError("raw_story_text 不能为空")

    _log_info("[story_pipeline] Step A1: premise compressor")
    a1_messages = [
        {"role": "system", "content": A1_PREMISE_COMPRESSOR_SYSTEM},
        {"role": "user", "content": A1_PREMISE_COMPRESSOR_USER_TMPL.format(raw_story=raw_story_text)},
    ]
    a1_text = call_model(a1_messages, stage_name="story_a1_premise").strip()

    _log_info("[story_pipeline] Step A2: alternate angles")
    a2_messages = [
        {"role": "system", "content": A2_ALT_ANGLES_SYSTEM},
        {"role": "user", "content": A2_ALT_ANGLES_USER_TMPL.format(a1_text=a1_text, raw_story=raw_story_text)},
    ]
    a2_text = call_model(a2_messages, stage_name="story_a2_angles").strip()

    # simplest merge: just concatenate A1 and A2; downstream steps treat it as "material"
    material_text = "\n\n".join([
        "[A1]", a1_text,
        "[A2]", a2_text,
    ])

    _log_info("[story_pipeline] Step A3: dimension selection (T2)")
    dimension_messages = [
        {"role": "system", "content": T2_DIMENSION_SYSTEM},
        {"role": "user", "content": T2_DIMENSION_USER_TMPL.format(material_text=material_text)},
    ]
    dimension_text = call_model(dimension_messages, stage_name="story_t2_dimension").strip()

    _log_info("[story_pipeline] Step A4: method selection (T3)")
    method_messages = [
        {"role": "system", "content": T3_METHOD_SYSTEM},
        {"role": "user", "content": T3_METHOD_USER_TMPL.format(material_text=material_text, dimension_text=dimension_text)},
    ]
    method_text = call_model(method_messages, stage_name="story_t3_method").strip()

    _log_info("[story_pipeline] Step A5: mechanism design (T4)")
    mechanism_messages = [
        {"role": "system", "content": T4_MECHANISM_SYSTEM},
        {"role": "user", "content": T4_MECHANISM_USER_TMPL.format(
            material_text=material_text,
            dimension_text=dimension_text,
            method_text=method_text,
        )},
    ]
    structure_text = call_model(mechanism_messages, stage_name="story_t4_mechanism").strip()

    _log_info("[story_pipeline] Step B: draft writing")
    draft_messages = [
        {"role": "system", "content": DRAFT_SYSTEM},
        {"role": "user", "content": DRAFT_USER_TMPL.format(structure_text=structure_text)},
    ]
    draft_text = call_model(draft_messages, stage_name="story_draft")

    _log_info("[story_pipeline] Step C: editing")
    core_premise = extract_core_premise(structure_text)
    edit_messages = [
        {"role": "system", "content": EDIT_SYSTEM},
        {"role": "user", "content": EDIT_USER_TMPL.format(core_premise=core_premise, draft_text=draft_text)},
    ]
    final_text = call_model(edit_messages, stage_name="story_edit").strip()

    return PunchlineResult(
        raw_story=raw_story_text.strip(),
        structure_text=structure_text.strip(),
        draft_text=draft_text.strip(),
        final_text=final_text,
        draft_stats=text_stats(draft_text),
        final_stats=text_stats(final_text),
    )


# ------------------------------
# CLI/demo helper
# ------------------------------

DEFAULT_STORY_001 = """昨天晚上打车回家，司机一路上都在跟语音助手吵架，他开着导航却每个路口都要问我是不是忽悠他。最后到小区门口他把车停下来说“你先下去确认这是不是你家”。"""
DEFAULT_STORY_002 = '''
那年我刚失业，又跟家里人大吵了一架，觉得自己的人生彻底完蛋了。
深夜不想回家，我买了一打啤酒，独自坐在漆黑的楼道台阶上，准备大哭一场来宣泄情绪。
我坐下来，眼泪刚涌出来，楼道的声控灯突然灭了。
四周一片死寂的黑，我那种悲伤的氛围瞬间被打断了。为了能看清手里的啤酒，也为了给自己壮胆，我不得不重重地跺了一下脚。
灯亮了。我酝酿情绪，继续哭。
过了三十秒，灯又灭了。
我不得不一边抽泣，一边再次用力跺脚。
那天晚上的场景是这样的：一个绝望的成年人，坐在楼梯上，每隔三十秒就要暂停悲伤，愤怒地跺一下脚，把灯跺亮，然后抓紧时间继续哭。
跺到最后，我脚都麻了，累得连哭的力气都没有了，只能骂骂咧咧地回家睡觉。
'''


def main() -> None:
    story = DEFAULT_STORY_002

    result = generate_punchline_from_story(story)

    _print_separator("RAW STORY")
    print(result.raw_story)

    _print_separator("STRUCTURE (Call_A)")
    print(result.structure_text)

    _print_separator(f"DRAFT (Call_B)  stats={result.draft_stats}")
    print(result.draft_text)

    _print_separator(f"FINAL (Call_C)  stats={result.final_stats}")
    print(result.final_text)


if __name__ == "__main__":
    # 项目启动时初始化日志
    setup_logging()
    main()

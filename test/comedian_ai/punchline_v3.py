"""test/comedian_ai/punchline_story.py

Raw-story → multi-step punchline generator.

Use case: feed in一段用户口述文本（无结构），模型分三步：
1. 理解 & 规划结构
2. 根据结构写草稿
3. 严苛编辑输出最终段子
"""

from __future__ import annotations

import os
import re
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


# ------------------------------
# T2 (v2 focus): Select → Generate
# ------------------------------

T2S_SELECT_SYSTEM = """你是单口喜剧【T2-S：方法选择器】。
任务：基于材料[A1]+[A2]，对 A2 的三个角度分别选择 2 种不同的喜剧方法（总计 6 个）。

硬性规则：
- 你必须为每个角度选择 2 个方法：SELF / CONSPIRACY / ACTION 各 2 个。
- 单次任务里 6 个方法ID 必须全部不重复（全局去重）。
- 选择要“大乱”：不要只挑最常用的那几个（例如 2.1/3.1/4.2 这种别老霸榜），优先尝试不那么常用但仍然能写出好笑结构的方法。
- 只做选择，不要生成 BEAT_SHEET，不要写段子。

可选方法清单（只能从这里选，照抄“ID 名称”）：
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

输出格式（严格照抄，必须只有这3行，禁止多余解释）：
SELF: <ID 名称> | <ID 名称>
CONSPIRACY: <ID 名称> | <ID 名称>
ACTION: <ID 名称> | <ID 名称>
"""

T2S_SELECT_USER_TMPL = """材料如下：
{material_text}

任务：按格式输出 6 个不重复的方法选择表。
"""

T2G_GENERATE_SYSTEM = """你是单口喜剧【T2-G：结构生成器】。
任务：你将收到：
1) 材料[A1]+[A2]
2) 一个已选好的“方法分配表”（SELF/CONSPIRACY/ACTION 各 2 个方法，总计 6 个，且不重复）

你要做的是：对 A2 的三个角度分别用分配到的 2 个方法，各生成 1 份【段子结构计划】。
最终总计输出 6 份结构计划。

硬性规则：
- 严格按分配表来生成：SELF 生成2份；CONSPIRACY 生成2份；ACTION 生成2份。
- 禁止新增事实/角色/剧情。
- 输出口语化，像舞台上能直接讲。
- “先选择再生成”：你只能使用分配表里的方法，禁止临时换方法/加方法。
- 每份计划都必须体现该方法的写法差异：不能六份都长得像同一个模板换皮。
- 不要输出长篇理论解释。

输出格式（严格照抄；顺序必须是 SELF(2份) → CONSPIRACY(2份) → ACTION(2份)）：
RESULTS:
- ANGLE_KEY: SELF
  METHOD: <ID 名称>
  CHOSEN_ANGLE_REF: <从A2的该角度里引用关键短语，1-2行>
  BEAT_SHEET:
  - <第1拍>
  - <第2拍>
  - <第3拍>
  - <第4拍>
  - <最后一句底句方向：一句话>
  KEY_CALLBACKS: ["...", "...", "..."]

- ANGLE_KEY: SELF
  METHOD: <ID 名称>
  CHOSEN_ANGLE_REF: <...>
  BEAT_SHEET:
  - <...>
  - <最后一句底句方向：一句话>
  KEY_CALLBACKS: ["...", "...", "..."]

- ANGLE_KEY: CONSPIRACY
  METHOD: <ID 名称>
  ...（同上）

- ANGLE_KEY: CONSPIRACY
  METHOD: <ID 名称>
  ...（同上）

- ANGLE_KEY: ACTION
  METHOD: <ID 名称>
  ...（同上）

- ANGLE_KEY: ACTION
  METHOD: <ID 名称>
  ...（同上）
"""

T2G_GENERATE_USER_TMPL = """材料如下：
{material_text}

方法分配表（必须严格使用，不得更改）：
{selection_text}

任务：按格式输出 RESULTS（6份结构计划）。
"""


# ------------------------------
# T3 (v3 focus): Two packs (A/B) in one call
# ------------------------------

T3_TWO_PACKS_SYSTEM = """你是单口喜剧【T3：双方案挑选+成稿（一段完成）】。
任务：你将收到：
1) 材料[A1]+[A2]
2) T2-G 生成的 6 份【段子结构计划】（按出现顺序编号为 1..6）

你要做的是：输出【两个】最终稿方案（A 和 B），每个方案都：
- 从 1..6 中挑选 3 个编号
- 用这 3 个计划整合成一篇递进的最终口语稿

硬性规则：
- 只允许输出 4 行（严格按顺序）：PICKS_A / SCRIPT_A / PICKS_B / SCRIPT_B。禁止多余解释。
- PICKS_A 必须恰好 3 个编号，用英文逗号分隔，例如：PICKS_A: 1,3,5。
- PICKS_B 必须恰好 3 个编号，用英文逗号分隔。
- “完全不同”：PICKS_A 与 PICKS_B 必须完全不重叠（交集为空），也就是两套加起来覆盖 6 个。
- 两套的编号都必须在 1..6 且各自不重复。
- SCRIPT_A / SCRIPT_B 都必须是一整段口语稿：不要项目符号、不要分行；允许少量括号动作（如（跺脚）（停顿））。
- 必须递进：每个 SCRIPT 内部都要逐步升级并收束。
- 严禁新增事实/角色/剧情。
- 不要解释方法论，直接写稿。
"""

T3_TWO_PACKS_USER_TMPL = """材料如下：
{material_text}

T2-G 输出（6份结构计划，按出现顺序编号 1..6）：
{t2_generate_text}

输出格式（严格照抄，仅 4 行）：
PICKS_A: 1,3,5
SCRIPT_A: <一整篇口语稿>
PICKS_B: 2,4,6
SCRIPT_B: <一整篇口语稿>
"""

# ------------------------------
# Legacy single-step T2 (kept for reference; user may have customized)
# ------------------------------

T2_TECHNIQUE_PLANNER_SYSTEM = """你是单口喜剧【T2：段子结构规划器】。
目标：把[A1]+[A2]里“不同喜剧路径”落到一个可直接写稿的【段子结构计划】。
你不是选标签，你要给出“怎么讲”的节奏与落点。

你必须只选用 1 条 A2 的 ANGLE_TYPE（自嘲视角 / 阴谋视角 / 行动视角），并基于它输出结构。
你必须只选用 1 个【预期违背的十三种操作方法】（照抄ID与名称）。

硬性规则：
- 禁止新增事实/角色/剧情。
- 输出要口语化，像舞台上能直接讲。
- 必须把“技巧”变成具体写法：BEAT_SHEET 必须能直接喂给草稿写手。
- 最后一句必须是底句方向（不是完整段子，但要能当最后一句的方向）。
- 不要输出任何长篇理论解释。

### 【预期违背的十三种操作方法（还原版）】

**1.1 语义双关 (Double Entendres)**
*   **怎么用**：利用多义词的文字游戏，让观众在两个含义间产生逻辑错位。
*   **示例**：教练被问及对球员表现的处理（Execution）怎么看，他答：“**我觉得行（枪毙了行）**。”（注：Execution 兼具“处理”与“处决”之意）。

**1.2 简单真相 (Simple Truth)**
*   **怎么用**：利用观众对措辞的“过度解读”建立默认预期，随后抛出最直白、甚至赤裸的字面含义。
*   **示例**：“我至今记得我的第一次。这不，**就在我的信用卡账单上写着呢**。”（注：观众预期是爱情故事，真相是“买春”）。

**1.3 配对短语 (Paired Phrases)**
*   **怎么用**：利用节奏、押韵和音节配对，在相似的音律中塞入极具反差的社会评价。
*   **示例**：三位总统筹款时的假名：**Hope**（希望）、**Grope**（猥亵）、**Dope**（蠢货）。（注：利用 /əʊp/ 押韵揭露丑闻与偏见）。

**1.4 自相矛盾（语义类）(Paradox)**
*   **怎么用**：用相互矛盾的部分组成一句话，揭示某种荒谬的真实性。
*   **示例**：“她的**内心深处很浅薄**。”。

**2.1 反转 (Reverses)**
*   **怎么用**：在最后一刻切换逻辑角度，让观众感觉到被戏弄，瞬间打破脑中已建立的画面感。
*   **示例**：“我老婆在床上温柔地用指尖抚摸我的秀发——**但那时候我已经去上班了,因为我脱发！**”。

**2.2 三步定律 (Triples)**
*   **怎么用**：用两个逻辑相近的元素构建思维定势，在第三步抛出荒谬夸张的元素打破框架。
*   **示例**：介绍四大文学名著：**《三国演义》，《水浒传》，《哈利波特》**。

**2.3 比较和对比 (Compare & Contrast)**
*   **怎么用**：让复杂内容突然变简单。当观众预期你要认真阐述时，突然推翻期望，一笔带过。
*   **示例**：“我知道我的脸是复杂性肌肤……**而我男朋友则十分肯定——他有一张脸**。”。

**3.1 制造反差 (Incongruity)**
*   **怎么用**：将两个本不相关或完全相反的元素并列讨论，常用于赋予物体人格化特征。
*   **示例**：中国餐馆挂着牌子：“**地道中餐，西班牙语点餐**。”。

**3.2 喜剧讽刺 (Comedic Irony)**
*   **怎么用**：展示事态与期望的背离，或揭露权威内部存在的明显矛盾（观众知道真相而角色不知道）。
*   **示例**：牧师在精神病院告诉病人“**时刻有人看着你**”，而病人正是因为觉得有人盯着他才进的病院。

**3.3 自相矛盾（逻辑类）(Paradox)**
*   **怎么用**：展示一个执行路径上的死循环或逻辑悖论，让规则本身变得滑稽。
*   **示例**：“如果你的**电话有什么问题，请拨打这个电话号码**（打不通才需要修）”。

**4.1 制造优越感 (Superiority)**
*   **怎么用**：描述他人的愚蠢想法或行为（或自嘲），使观众产生智力或心理上的优势。
*   **示例**：一个哥们怕把钥匙揣右边兜里会显得像个同性恋（死gay），这种**充满偏见的逻辑**让观众感到对方很蠢。

**4.4 观察式喜剧 (Observation-Recognition)**
*   **怎么用**：抓住日常生活中人人都有强烈共鸣、却从未被提及的细节，放在“放大镜”下重现。
*   **示例**：“为什么我们每次**擤完鼻子后都要再看一眼餐巾纸**？”。

**4.3 绵里藏针 (Benign Retaliation)**
*   **怎么用**：在“假设”的情景下进行虚构的、无流血损伤的报复，找回场子。
*   **示例**：老婆因为清洁工要来而疯狂打扫，老公就在园丁来之前强迫老婆起床**铲草作为报复**。

**4.4 闹剧 (Slapstick)**
*   **怎么用**：利用夸张甚至愚蠢的肢体动作，通过物理层面的“呈现”让观众产生心理优势。
*   **示例**：在单口喜剧中通过**模仿或角色呈现 (Act-out)** 来展示一个滑稽的动作细节。

***
输出格式（严格照抄，逐行，禁止遗漏）：
CHOSEN_COMBO: <选用的角度类型> + <选用的方法ID与名称>
STRATEGY_RATIONALE: <1句：为什么这个技巧能放大这个角度？（例如：用“闹剧”是因为跺脚这个动作本身就很滑稽）>

BEAT_SHEET:
- [SETUP / 铺垫]: <建立背景与预期。必须包含具体的环境描写或人物状态，让观众信以为真。>
- [TRIGGER / 触发]: <引入那个“不对劲”的变量。这里要强调主角的“人设缺陷”是如何发作的。>
- [ESCALATION / 升级]: <顺着荒谬逻辑往下推。加入具体的“内心独白”或“脑补画面”，让事态变得更严重/更离谱。>

"""

T2_TECHNIQUE_PLANNER_USER_TMPL = """材料如下：
{material_text}

任务：按字段输出一个【段子结构计划】。
"""
# NOTE(v2): 后续步骤（T3/T4/DRAFT/EDIT）先全部不考虑。
# 你确认：v2 目前只专注把 A1+A2 变成高质量的 T2 段子结构计划。
#
# T3_METHOD_SYSTEM = """..."""
# T4_MECHANISM_SYSTEM = """..."""
# DRAFT_SYSTEM = """..."""
# EDIT_SYSTEM = """..."""


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
    a1_text: str
    a2_text: str
    t2_select_text: str
    t2_generate_text: str
    t3_text: str


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

    material_text = "\n\n".join([
        "[A1]", a1_text,
        "[A2]", a2_text,
    ])

    _log_info("[story_pipeline] Step T2-S: select methods")
    t2s_messages = [
        {"role": "system", "content": T2S_SELECT_SYSTEM},
        {"role": "user", "content": T2S_SELECT_USER_TMPL.format(material_text=material_text)},
    ]
    t2_select_text = call_model(t2s_messages, stage_name="story_t2_select").strip()

    # validate: must contain 6 unique method IDs like "2.1"
    method_ids = re.findall(r"\b\d\.\d\b", t2_select_text)
    if len(method_ids) != 6 or len(set(method_ids)) != 6:
        raise ValueError(
            "T2-S 输出不符合要求：需要 6 个不重复的方法ID（例如 2.1），并严格按 3 行格式输出。\n"
            f"t2_select_text=\n{t2_select_text}"
        )

    _log_info("[story_pipeline] Step T2-G: generate 6 structure plans")
    t2g_messages = [
        {"role": "system", "content": T2G_GENERATE_SYSTEM},
        {"role": "user", "content": T2G_GENERATE_USER_TMPL.format(material_text=material_text, selection_text=t2_select_text)},
    ]
    t2_generate_text = call_model(t2g_messages, stage_name="story_t2_generate").strip()

    _log_info("[story_pipeline] Step T3: two packs pick+script (single call)")
    t3_messages = [
        {"role": "system", "content": T3_TWO_PACKS_SYSTEM},
        {"role": "user", "content": T3_TWO_PACKS_USER_TMPL.format(material_text=material_text, t2_generate_text=t2_generate_text)},
    ]
    t3_text = call_model(t3_messages, stage_name="story_t3_two_packs").strip()

    # validate picks: two disjoint sets, each exactly 3 unique numbers in 1..6
    ma = re.search(r"^PICKS_A:\s*([1-6](?:\s*,\s*[1-6])*)\s*$", t3_text, flags=re.MULTILINE)
    mb = re.search(r"^PICKS_B:\s*([1-6](?:\s*,\s*[1-6])*)\s*$", t3_text, flags=re.MULTILINE)
    if not ma or not mb:
        raise ValueError(f"T3 输出不符合格式：缺少合法的 PICKS_A / PICKS_B 行。\n t3_text=\n{t3_text}")
    picks_a = [int(x.strip()) for x in ma.group(1).split(",")]
    picks_b = [int(x.strip()) for x in mb.group(1).split(",")]
    if len(picks_a) != 3 or len(set(picks_a)) != 3:
        raise ValueError(f"T3 PICKS_A 不符合要求：需要恰好 3 个且不重复。\n t3_text=\n{t3_text}")
    if len(picks_b) != 3 or len(set(picks_b)) != 3:
        raise ValueError(f"T3 PICKS_B 不符合要求：需要恰好 3 个且不重复。\n t3_text=\n{t3_text}")
    if set(picks_a) & set(picks_b):
        raise ValueError(f"T3 两套 PICKS 必须完全不同（不得重叠）。\n t3_text=\n{t3_text}")

    return PunchlineResult(
        raw_story=raw_story_text.strip(),
        a1_text=a1_text.strip(),
        a2_text=a2_text.strip(),
        t2_select_text=t2_select_text.strip(),
        t2_generate_text=t2_generate_text.strip(),
        t3_text=t3_text.strip(),
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
DEFAULT_STORY_003 = '''
马上就是元旦了,从国庆节以后,这是三个月第一次放假很开心
但是每次放假都要调休,想一想就难受
感觉放假恢复的电量,连续上六天班直接 耗尽
'''


def main() -> None:
    story = DEFAULT_STORY_003

    result = generate_punchline_from_story(story)

    _print_separator("RAW STORY")
    print(result.raw_story)

    _print_separator("A1")
    print(result.a1_text)

    _print_separator("A2")
    print(result.a2_text)

    _print_separator("T2-S (SELECT)")
    print(result.t2_select_text)

    _print_separator("T2-G (GENERATE)")
    print(result.t2_generate_text)

    _print_separator("T3 (PICK+SCRIPT)")
    print(result.t3_text)


if __name__ == "__main__":
    # 项目启动时初始化日志
    setup_logging()
    main()

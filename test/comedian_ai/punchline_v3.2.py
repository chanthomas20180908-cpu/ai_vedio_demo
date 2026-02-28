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
from typing import Dict, List, Tuple

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

A2_ALT_ANGLES_SYSTEM = """你是单口喜剧“梗概发散器”。你的任务是基于【原始故事】，分裂出 3 条完全不同的喜剧解释路径。

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

A2_ALT_ANGLES_USER_TMPL = """原始故事（不要改写，只供理解）：
{raw_story}

任务：按字段输出 A2。
"""


# ------------------------------
# T2 (v2 focus): Select → Generate
# ------------------------------

T2S_SELECT_SYSTEM = """你是单口喜剧【T2-S：方法选择器】。
任务：基于材料[RAW_STORY]+[A2]，对 A2 的三个角度分别选择 2 种不同的喜剧方法（总计 6 个）。

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

# T2-G (v3.1): generate 6 plans via 6 calls (one plan per call) + method description+example.
# NOTE: We keep the output item schema identical to previous T2-G items so T3 remains unchanged.

# Per-method full description + example (for model understanding).
# Source of truth: the verbatim text inside T2_TECHNIQUE_PLANNER_SYSTEM.
# NOTE: T2_TECHNIQUE_PLANNER_SYSTEM has a numbering mismatch where "观察式喜剧" is labeled as 4.4.
# We map that verbatim block to method_id "4.2" for compatibility with the T2-S selection list.

# 版本留存:尝试让AI生成了一版本,让AI更能理解
# METHOD_DESC_EXAMPLES: Dict[str, str] = {
#     "1.1": """**1.1 语义双关 (Double Entendres)**
# *   **怎么用**：利用多义词的文字游戏，让观众在两个含义间产生逻辑错位。
# *   **示例**：教练被问及对球员表现的处理（Execution）怎么看，他答：“**我觉得行（枪毙了行）**。”（注：Execution 兼具“处理”与“处决”之意）。""",
#     "1.2": """**1.2 简单真相 (Simple Truth)**
# *   **怎么用**：利用观众对措辞的“过度解读”建立默认预期，随后抛出最直白、甚至赤裸的字面含义。
# *   **示例**：“我至今记得我的第一次。这不，**就在我的信用卡账单上写着呢**。”（注：观众预期是爱情故事，真相是“买春”）。""",
#     "1.3": """**1.3 配对短语 (Paired Phrases)**
# *   **怎么用**：利用节奏、押韵和音节配对，在相似的音律中塞入极具反差的社会评价。
# *   **示例**：三位总统筹款时的假名：**Hope**（希望）、**Grope**（猥亵）、**Dope**（蠢货）。（注：利用 /əʊp/ 押韵揭露丑闻与偏见）。""",
#     "1.4": """**1.4 自相矛盾（语义类）(Paradox)**
# *   **怎么用**：用相互矛盾的部分组成一句话，揭示某种荒谬的真实性。
# *   **示例**：“她的**内心深处很浅薄**。”。""",
#     "2.1": """**2.1 反转 (Reverses)**
# *   **怎么用**：在最后一刻切换逻辑角度，让观众感觉到被戏弄，瞬间打破脑中已建立的画面感。
# *   **示例**：“我老婆在床上温柔地用指尖抚摸我的秀发——**但那时候我已经去上班了,因为我脱发！**”。""",
#     "2.2": """**2.2 三步定律 (Triples)**
# *   **怎么用**：用两个逻辑相近的元素构建思维定势，在第三步抛出荒谬夸张的元素打破框架。
# *   **示例**：介绍四大文学名著：**《三国演义》，《水浒传》，《哈利波特》**。""",
#     "2.3": """**2.3 比较和对比 (Compare & Contrast)**
# *   **怎么用**：让复杂内容突然变简单。当观众预期你要认真阐述时，突然推翻期望，一笔带过。
# *   **示例**：“我知道我的脸是复杂性肌肤……**而我男朋友则十分肯定——他有一张脸**。”。""",
#     "3.1": """**3.1 制造反差 (Incongruity)**
# *   **怎么用**：将两个本不相关或完全相反的元素并列讨论，常用于赋予物体人格化特征。
# *   **示例**：中国餐馆挂着牌子：“**地道中餐，西班牙语点餐**。”。""",
#     "3.2": """**3.2 喜剧讽刺 (Comedic Irony)**
# *   **怎么用**：展示事态与期望的背离，或揭露权威内部存在的明显矛盾（观众知道真相而角色不知道）。
# *   **示例**：牧师在精神病院告诉病人“**时刻有人看着你**”，而病人正是因为觉得有人盯着他才进的病院。""",
#     "3.3": """**3.3 自相矛盾（逻辑类）(Paradox)**
# *   **怎么用**：展示一个执行路径上的死循环或逻辑悖论，让规则本身变得滑稽。
# *   **示例**：“如果你的**电话有什么问题，请拨打这个电话号码**（打不通才需要修）”。""",
#     "4.1": """**4.1 制造优越感 (Superiority)**
# *   **怎么用**：描述他人的愚蠢想法或行为（或自嘲），使观众产生智力或心理上的优势。
# *   **示例**：一个哥们怕把钥匙揣右边兜里会显得像个同性恋（死gay），这种**充满偏见的逻辑**让观众感到对方很蠢。""",
#     "4.2": """**4.4 观察式喜剧 (Observation-Recognition)**
# *   **怎么用**：抓住日常生活中人人都有强烈共鸣、却从未被提及的细节，放在“放大镜”下重现。
# *   **示例**：“为什么我们每次**擤完鼻子后都要再看一眼餐巾纸**？”。""",
#     "4.3": """**4.3 绵里藏针 (Benign Retaliation)**
# *   **怎么用**：在“假设”的情景下进行虚构的、无流血损伤的报复，找回场子。
# *   **示例**：老婆因为清洁工要来而疯狂打扫，老公就在园丁来之前强迫老婆起床**铲草作为报复**。""",
#     "4.4": """**4.4 闹剧 (Slapstick)**
# *   **怎么用**：利用夸张甚至愚蠢的肢体动作，通过物理层面的“呈现”让观众产生心理优势。
# *   **示例**：在单口喜剧中通过**模仿或角色呈现 (Act-out)** 来展示一个滑稽的动作细节。""",
# }
METHOD_DESC_EXAMPLES: Dict[str, str] = {
#     "1.1": """**1.1 语义双关 (Double Entendres)**
# *   **核心逻辑**：一个词，两种理解（表层意思 vs 深层/禁忌意思）。
# *   **怎么用**：找到一个多义词（如“干”、“意思”、“硬”），先铺垫正常的语境，然后突然切换到另一个含义。
# *   **示例**：面试官问我：“你在上一份工作中最大的成就是什么？”我答：“**我帮老板背了不少锅（黑锅/锅具）**，毕竟我是个厨师。”""",
#
    "1.2": """**1.2 简单真相 (Simple Truth)**
*   **核心逻辑**：诗意的铺垫 + 极其物质/现实的真相。
*   **怎么用**：先用文艺、宏大的词汇描述一个场景，让观众以为你要煽情，最后用一个具体的、甚至庸俗的物体打破它。
*   **示例**：“我的前任偷走了我的心，**顺便还偷走了我的支付宝密码**。”""",

    "1.3": """**1.3 配对短语 (Paired Phrases)**
*   **核心逻辑**：工整的对仗结构（A是X，B是Y）。
*   **怎么用**：使用排比句式。前半句建立一个高大上的形象，后半句用同样的句式接一个极其拉垮的形象，形成节奏感。
*   **示例**：“理想很丰满，**现实很骨感**；老板画饼画得像毕加索，**我吃饼吃得像武大郎**。”""",

    "1.4": """**1.4 自相矛盾（语义类）(Paradox)**
*   **核心逻辑**：形容词 + 反义名词 = 荒谬的画面。
*   **怎么用**：将两个根本不可能共存的状态硬塞进一个人或一件事里，揭示其虚伪。
*   **示例**：“他是一个**诚实的骗子**：他骗我说爱我，然后**诚实地跟别人跑了**。”""",

    "2.1": """**2.1 反转 (Reverses)**
*   **核心逻辑**：误导铺垫（Setup） -> 惯性思维 -> 意外结局（Punchline）。
*   **怎么用**：讲一个故事，让观众以为结局是A，在最后半句话突然揭示结局其实是B，而且B能解释前面的铺垫。
*   **示例**：“我想像我爷爷那样，在睡梦中安详地离去……**而不是像他车里的乘客那样尖叫着挂掉**。”""",

    "2.2": """**2.2 三步定律 (Triples)**
*   **核心逻辑**：正常 A -> 正常 B -> 荒谬 C。
*   **怎么用**：列举三个事物。前两个建立一个严肃或正常的模式，第三个突然打破模式，加入一个离谱的东西。
*   **示例**：“为了健康，我每天坚持做三件事：吃早餐、跑步、**以及对路边的狗做鬼脸**。”""",

    "2.3": """**2.3 比较和对比 (Compare & Contrast)**
*   **核心逻辑**：高大上 vs 矮矬穷。
*   **怎么用**：将一个复杂、高级的概念，和一个简单、低级的概念并列，突出后者的可笑或无奈。
*   **示例**：“蝙蝠侠有蝙蝠车，蜘蛛侠有蛛丝，**而我有……公交卡**。”""",

#     "3.1": """**3.1 制造反差 (Incongruity)**
# *   **核心逻辑**：错误的地点 + 错误的人/事。
# *   **怎么用**：把一个角色或物体放在它绝对不该出现的地方，或者让它做绝对不符合身份的事。
# *   **示例**：“就像一个和尚**走进脱衣舞俱乐部去化缘**。”""",
#
#     "3.2": """**3.2 喜剧讽刺 (Comedic Irony)**
# *   **核心逻辑**：意图与结果截然相反。
# *   **怎么用**：描述一个人为了达成目标A，努力做了很多事，结果恰恰导致了相反的结果B。
# *   **示例**：“消防局**着火了**”；或者“婚姻咨询师**正在闹离婚**”。""",
#
#     "3.3": """**3.3 自相矛盾（逻辑类）(Paradox)**
# *   **核心逻辑**：死循环（Catch-22）。
# *   **怎么用**：制定一个永远无法执行的规则，或者描述一个只有当你不需要时才能得到的条件。
# *   **示例**：“这台打印机只有在**你不需要打印急件的时候**，工作得最顺畅。”""",
#
#     "4.1": """**4.1 制造优越感 (Superiority)**
# *   **核心逻辑**：展示他人的愚蠢，让观众感到自己更聪明。
# *   **怎么用**：描述一个人（或过去的自己）因为无知、偏见而做出的蠢事。
# *   **示例**：“我朋友以为‘手动挡’的意思是**车坏了他得下来推**。”""",
#
#     "4.2": """**4.4 观察式喜剧 (Observation-Recognition)**
# *   **核心逻辑**：难道只有我一个人觉得……？
# *   **怎么用**：指出生活中那些极其微小、大家习以为常但其实很荒谬的细节。通常以“你们有没有发现……”开头。
# *   **示例**：“为什么遥控器没电的时候，**我们都会用力地按按钮？难道用力能把电挤出来吗？**”""",
#
#     "4.3": """**4.3 绵里藏针 (Benign Retaliation)**
# *   **核心逻辑**：小人物的无害报复。
# *   **怎么用**：面对无法改变的压迫（如老板、老婆），用一种极其幼稚、微小的方式进行精神胜利法的报复。
# *   **示例**：“老板让我加班不给钱，我就**在公司上厕所把马桶冲了这辈子最多次的水**，冲垮他的水费预算。”""",
#
#     "4.4": """**4.4 闹剧 (Slapstick)**
# *   **核心逻辑**：文字描述的肢体滑稽。
# *   **怎么用**：用文字生动地描绘一个笨拙的动作、摔倒、或物理上的尴尬瞬间。
# *   **示例**：“我试图帅气地靠在墙上跟美女搭讪，**结果完全没靠住，整个人像一滩泥一样滑到了地上**。”""",
}


T2G_ONE_SYSTEM = '''
你的身份是【金句炼金术士】。你的任务不是讲故事，而是**提炼**。你要利用指定的【喜剧方法】，将用户输入的原始素材（A1）压缩成一个**短小、精悍、甚至有点毒舌的喜剧金句（Punchline）**。

# Inputs
原始素材 + 指定喜剧方法

# Critical Rules (铁律)
1. **拒绝解释：** 不要写“这里运用了...”，不要写“铺垫是...”。直接给我那个结果。
2. **拒绝啰嗦：** 字数严格控制在 60 字以内。能用一句话说完，绝不分两句。
3. **技巧强制：** 必须明显地使用指定的 [METHOD]。
4. **拒绝书面语：** 必须是口语，必须像是在脱口秀舞台上拿着麦克风说出来的。

# Output Format (Strict JSON-like Text)
- METHOD: <ID 名称>
  THE_BIT: <最终生成的金句/段子。不要包含动作指导，只要台词。>
  WHY_IT_WORKS: <用一句话解释这个金句是如何精准命中该喜剧方法的>
'''
# 版本留存:问题是输出太长了,是一个哽完整的段子结构,但是缺少爆点,缺少对喜剧方法的遵从
# '''
# # Role
# 你的任务是【喜剧增幅】。你要利用指定的【喜剧方法】，将用户输入的原始素材（A1/A2）打磨成一个**幽默,炸裂,画面感极强**的段子结构。
#
# # Inputs
# 基础的段子素材+新增喜剧方法
#
# # Task
# 输出 1 份【段子结构计划】。
# **核心要求：不要解释笑话，要制造笑话。**
# 在 BEAT_SHEET 的每一拍中，不要写“这里要用比喻”，而要**直接写出那个比喻是什么**；不要写“这里要表达愤怒”，而要**写出愤怒的具体台词或动作**。
#
# # Critical Rules (铁律)
# 1. **拒绝抽象：** 严禁出现“矛盾感”、“讽刺性”、“夸张手法”等学术名词。必须替换为**大白话、具体物体、生活场景**。（❌“表达了我的贪婪” -> ✅“我就像个护食的野狗”）
# 2. **技巧落地：** 必须用指定的 [METHOD] 重新改写素材，而不是生硬地套用。如果技巧是“自相矛盾”，你必须找出那个具体的矛盾点并放大。
# 3. **情绪递进：** 每一拍的情绪必须比上一拍更强烈、更荒谬。
# 4. **口语化：** 所有的描述必须像是在这就地表演，而不是写论文。
#
# # Output Format (Strict JSON-like Text)
# - ANGLE_KEY: <SELF|CONSPIRACY|ACTION>
#   METHOD: <ID 名称>
#   CHOSEN_ANGLE_REF: <引用素材中最有潜力的一句话>
#   BEAT_SHEET:
#   - <铺垫：用最简短的话建立情境，必须包含具体的画面细节>
#   - <翻番1：利用 METHOD 制造第一个笑点/槽点，必须具体>
#   - <翻番2：情绪升级，引入更离谱的比喻或逻辑，必须具体>
#   - <Act-out/高潮：具体的表演动作、模仿或夸张的台词>
#   - <底句/收束：一句冷峻的、或极其荒谬的总结>
#   KEY_CALLBACKS: ["<关键词1>", "<关键词2>", "<关键词3>"]
# '''

'''
你的身份是【金句炼金术士】。你的任务不是讲故事，而是**提炼**。你要利用指定的【喜剧方法】，将用户输入的原始素材（A1）压缩成一个**短小、精悍、甚至有点毒舌的喜剧金句（Punchline）**。

# Inputs
原始素材 + 指定喜剧方法

# Critical Rules (铁律)
1. **拒绝解释：** 不要写“这里运用了...”，不要写“铺垫是...”。直接给我那个结果。
2. **拒绝啰嗦：** 字数严格控制在 60 字以内。能用一句话说完，绝不分两句。
3. **技巧强制：** 必须明显地使用指定的 [METHOD]。
4. **拒绝书面语：** 必须是口语，必须像是在脱口秀舞台上拿着麦克风说出来的。

# Output Format (Strict JSON-like Text)
- METHOD: <ID 名称>
  THE_BIT: <最终生成的金句/段子。不要包含动作指导，只要台词。>
  WHY_IT_WORKS: <用一句话解释这个金句是如何精准命中该喜剧方法的>
'''

T2G_ONE_USER_TMPL = """[RAW_STORY]
{raw_story}

[A2_ANGLE]
{a2_angle_text}

METHOD_CHOSEN: {method_id} {method_name}

METHOD_DESC_AND_EXAMPLE:
{method_desc}

任务：按格式输出 1 份结构计划，ANGLE_KEY 必须是 {angle_key}，METHOD 必须是 {method_id} {method_name}。
"""


# ------------------------------
# T3 (v3.1 focus): Three scripts from 6 plans, as 3 disjoint pairs (single call)
# ------------------------------

T3_THREE_PAIRS_SYSTEM = """你是单口喜剧【T3：三方案配对挑选+成稿（一段完成）】。
任务：你将收到：
1) 材料[RAW_STORY]+[A2]
2) T2-G 生成的 6 份【段子结构计划】（按出现顺序编号为 1..6）

你要做的是：输出【三个】最终稿方案（A / B / C），每个方案都：
- 从 1..6 中挑选 2 个编号
- 用这 2 个计划整合成一篇递进的最终口语稿

硬性规则（为了稳定解析，请严格遵守）：
- 你必须只输出 6 行，且顺序固定如下：
  1) PICKS_A: <digit>,<digit>
  2) SCRIPT_A: <single-line monologue>
  3) PICKS_B: <digit>,<digit>
  4) SCRIPT_B: <single-line monologue>
  5) PICKS_C: <digit>,<digit>
  6) SCRIPT_C: <single-line monologue>
- 每个 PICKS_* 必须是“数字,数字”，必须使用英文冒号 ':' 与英文逗号 ','，逗号两侧不要空格（例如：PICKS_A: 1,4）。
- 三套 PICKS 必须两两不重叠，并且三套加起来必须刚好覆盖 6 个编号（把 1..6 配成 3 对）。
- SCRIPT_* 每条都必须是一整段口语稿：禁止换行、禁止项目符号；允许少量括号动作（如（跺脚）（停顿））。
- 每个 SCRIPT 内部必须递进并收束。
- 严禁新增事实/角色/剧情。
- 不要解释方法论，直接写稿。
"""

T3_THREE_PAIRS_USER_TMPL = """材料如下：
{material_text}

T2-G 输出（6份结构计划，按出现顺序编号 1..6）：
{t2_generate_text}

你必须严格按以下格式输出（只允许 6 行，顺序固定，禁止多余解释；SCRIPT 行禁止换行）：
PICKS_A: 1,4
SCRIPT_A: <一整段口语稿>
PICKS_B: 2,6
SCRIPT_B: <一整段口语稿>
PICKS_C: 3,5
SCRIPT_C: <一整段口语稿>
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
            model_type="qwen",
            model="qwen-max",
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


def _parse_t2_selection_table(t2_select_text: str) -> List[Tuple[str, str, str]]:
    """Parse T2-S 3-line table into ordered (ANGLE_KEY, method_id, method_name) list.

    Order is fixed: SELF(2) -> CONSPIRACY(2) -> ACTION(2).
    """

    def _get_line(prefix: str) -> str:
        for ln in t2_select_text.splitlines():
            if ln.strip().startswith(prefix):
                return ln.strip()
        raise ValueError(f"T2-S 输出缺少 {prefix} 行。\n t2_select_text=\n{t2_select_text}")

    def _parse_two_methods(line: str) -> List[Tuple[str, str]]:
        # e.g. "SELF: 1.3 配对短语 | 3.3 自相矛盾（逻辑类）"
        payload = line.split(":", 1)[1].strip()
        parts = [p.strip() for p in payload.split("|")]
        if len(parts) != 2:
            raise ValueError(f"T2-S 行格式错误：需要两个方法，用 | 分隔。\n line={line}")
        out: List[Tuple[str, str]] = []
        for p in parts:
            mid = re.search(r"\b\d\.\d\b", p)
            if not mid:
                raise ValueError(f"T2-S 方法缺少ID（例如 2.1）。\n line={line}")
            method_id = mid.group(0)
            method_name = p.replace(method_id, "", 1).strip()
            if not method_name:
                raise ValueError(f"T2-S 方法缺少名称。\n line={line}")
            out.append((method_id, method_name))
        return out

    mapping = [
        ("SELF", "SELF:"),
        ("CONSPIRACY", "CONSPIRACY:"),
        ("ACTION", "ACTION:"),
    ]

    triples: List[Tuple[str, str, str]] = []
    for angle_key, prefix in mapping:
        line = _get_line(prefix)
        for method_id, method_name in _parse_two_methods(line):
            triples.append((angle_key, method_id, method_name))

    if len(triples) != 6:
        raise ValueError(f"T2-S 解析失败：需要 6 个方法。\n t2_select_text=\n{t2_select_text}")
    if len({m for _, m, _ in triples}) != 6:
        raise ValueError(f"T2-S 解析失败：6 个方法ID 必须全局不重复。\n t2_select_text=\n{t2_select_text}")

    return triples


def _extract_a2_angle_block(a2_text: str, angle_key: str) -> str:
    angle_type_map = {
        "SELF": "自嘲视角",
        "CONSPIRACY": "阴谋视角",
        "ACTION": "行动视角",
    }
    angle_type = angle_type_map.get(angle_key)
    if not angle_type:
        raise ValueError(f"未知 ANGLE_KEY: {angle_key}")

    needle = f"- ANGLE_TYPE: {angle_type}"
    start = a2_text.find(needle)
    if start < 0:
        raise ValueError(f"A2 中找不到 {needle}。\n a2_text=\n{a2_text}")

    # Next block starts with a blank line then another "- ANGLE_TYPE:".
    next_marker = "\n\n- ANGLE_TYPE:"
    end = a2_text.find(next_marker, start + len(needle))
    if end < 0:
        end = len(a2_text)

    return a2_text[start:end].strip()


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
    a2_text: str
    t2_select_text: str
    t2_generate_text: str
    t3_text: str


def generate_punchline_from_story(raw_story_text: str) -> PunchlineResult:
    if not raw_story_text.strip():
        raise ValueError("raw_story_text 不能为空")

    _log_info("[story_pipeline] Step A2: alternate angles")
    a2_messages = [
        {"role": "system", "content": A2_ALT_ANGLES_SYSTEM},
        {"role": "user", "content": A2_ALT_ANGLES_USER_TMPL.format(raw_story=raw_story_text)},
    ]
    a2_text = call_model(a2_messages, stage_name="story_a2_angles").strip()

    material_text = "\n\n".join([
        "[RAW_STORY]", raw_story_text.strip(),
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

    _log_info("[story_pipeline] Step T2-G: generate 6 structure plans (6 calls)")

    # Build 6 tasks in a fixed order: SELF(2) -> CONSPIRACY(2) -> ACTION(2)
    tasks = _parse_t2_selection_table(t2_select_text)

    t2_items: List[str] = []
    for idx, (angle_key, method_id, method_name) in enumerate(tasks, start=1):
        a2_angle_text = _extract_a2_angle_block(a2_text, angle_key)
        method_desc = METHOD_DESC_EXAMPLES.get(method_id)
        if not method_desc:
            raise ValueError(f"缺少方法说明+示例：{method_id}。请在 METHOD_DESC_EXAMPLES 中补齐。")

        _log_info(f"[story_pipeline] Step T2-G({idx}/6): {angle_key} {method_id} {method_name}")
        one_messages = [
            {"role": "system", "content": T2G_ONE_SYSTEM},
            {
                "role": "user",
                "content": T2G_ONE_USER_TMPL.format(
                    raw_story=raw_story_text.strip(),
                    a2_angle_text=a2_angle_text,
                    angle_key=angle_key,
                    method_id=method_id,
                    method_name=method_name,
                    method_desc=method_desc,
                ),
            },
        ]
        one_text = call_model(one_messages, stage_name=f"story_t2_generate_{idx}").strip()

        # NOTE: user requested to comment out validation here.
        # first_nonempty = next((ln for ln in one_text.splitlines() if ln.strip()), "")
        # expected_first = f"- ANGLE_KEY: {angle_key}"
        # if first_nonempty.strip() != expected_first:
        #     raise ValueError(
        #         "T2-G 单次输出不符合格式：第一行必须严格是 "
        #         f"'{expected_first}'。\n one_text=\n{one_text}"
        #     )
        # if f"METHOD: {method_id} {method_name}" not in one_text:
        #     raise ValueError(
        #         "T2-G 单次输出不符合格式：必须包含正确的 METHOD 行。\n"
        #         f" one_text=\n{one_text}"
        #     )

        t2_items.append(one_text)

    t2_generate_text = "RESULTS:\n" + "\n\n".join(t2_items)

    # _log_info("[story_pipeline] Step T3: three scripts via disjoint pairs (single call)")
    # t3_messages = [
    #     {"role": "system", "content": T3_THREE_PAIRS_SYSTEM},
    #     {"role": "user", "content": T3_THREE_PAIRS_USER_TMPL.format(material_text=material_text, t2_generate_text=t2_generate_text)},
    # ]
    # t3_text = call_model(t3_messages, stage_name="story_t3_three_pairs").strip()
    #
    # # validate T3 output using the simplest stable parsing:
    # # - must be exactly 6 lines
    # # - fixed prefixes and order
    # # - PICKS line payload is "d,d" (comma-separated)
    # lines = [ln.rstrip("\r") for ln in t3_text.splitlines() if ln.strip() != ""]
    # if len(lines) != 6:
    #     raise ValueError(
    #         "T3 输出不符合格式：必须严格只有 6 行（PICKS_A/SCRIPT_A/PICKS_B/SCRIPT_B/PICKS_C/SCRIPT_C）。\n"
    #         f"t3_text=\n{t3_text}"
    #     )
    #
    # expected_prefixes = [
    #     "PICKS_A:",
    #     "SCRIPT_A:",
    #     "PICKS_B:",
    #     "SCRIPT_B:",
    #     "PICKS_C:",
    #     "SCRIPT_C:",
    # ]
    # for i, prefix in enumerate(expected_prefixes):
    #     if not lines[i].startswith(prefix):
    #         raise ValueError(
    #             f"T3 输出不符合格式：第 {i+1} 行必须以 {prefix} 开头。\n"
    #             f"t3_text=\n{t3_text}"
    #         )
    #
    # def _parse_pair(line: str, prefix: str) -> List[int]:
    #     payload = line[len(prefix):].strip()
    #     parts = payload.split(",")
    #     if len(parts) != 2:
    #         raise ValueError(f"T3 {prefix} 后必须是两个编号，格式如 1,4。\n t3_text=\n{t3_text}")
    #     a = int(parts[0].strip())
    #     b = int(parts[1].strip())
    #     return [a, b]
    #
    # picks_a = _parse_pair(lines[0], "PICKS_A:")
    # picks_b = _parse_pair(lines[2], "PICKS_B:")
    # picks_c = _parse_pair(lines[4], "PICKS_C:")
    #
    # for label, picks in [("PICKS_A", picks_a), ("PICKS_B", picks_b), ("PICKS_C", picks_c)]:
    #     if len(set(picks)) != 2:
    #         raise ValueError(f"T3 {label} 不符合要求：两个编号必须不重复。\n t3_text=\n{t3_text}")
    #     if any((x < 1 or x > 6) for x in picks):
    #         raise ValueError(f"T3 {label} 不符合要求：编号必须在 1..6。\n t3_text=\n{t3_text}")
    #
    # union = set(picks_a) | set(picks_b) | set(picks_c)
    # if len(union) != 6:
    #     raise ValueError(
    #         "T3 三套 PICKS 必须两两不重叠并覆盖全部 6 个编号（把 1..6 配成三对）。\n"
    #         f"t3_text=\n{t3_text}"
    #     )

    return PunchlineResult(
        raw_story=raw_story_text.strip(),
        a2_text=a2_text.strip(),
        t2_select_text=t2_select_text.strip(),
        t2_generate_text=t2_generate_text.strip(),
        # t3_text=t3_text.strip(),
        t3_text="",
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
国庆之后这三个月，我一天假没放过，真的累透了。
刚听说元旦放三天，我第一反应是特高兴，终于能歇歇了。结果仔细一看通知：回来那个周日得补班。
心情立马就垮了。这三天里两天本来就是周末，剩下一天还得拿后面的周日去换。
一想到放完假回来，还得爬起来去上那个破班，然后连着干六天，我就特烦。这种“拆东墙补西墙”的放假，感觉比不放假还累，纯粹折腾人。
'''
DEFAULT_STORY_004 = '''
从国庆放假后,三个月都没有放过假期
平时不怎么关注放假信息
一般元旦是放一天,
一天工作期间,听同事说元旦放三天假期,很开心
就去看了以下日历,发现确实元旦放三天假
但是看到,放假回来的周日,又是调休上班
情绪很生气,
如果要放假,为什么不直接放,还要调休
放假回来,又要连续上6天班,真的很痛苦
一下感觉放假又不香了
还不如放一天假期,但是不要调休
'''


def main() -> None:
    story = DEFAULT_STORY_004

    result = generate_punchline_from_story(story)

    _print_separator("RAW STORY")
    print(result.raw_story)

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

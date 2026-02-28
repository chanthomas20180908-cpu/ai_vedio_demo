"""test/comedian_ai/punchline_story.py

Raw-story → multi-step punchline generator.

Use case: feed in一段用户口述文本（无结构），模型分三步：
1. 理解 & 规划结构
2. 根据结构写草稿
3. 严苛编辑输出最终段子
"""

from __future__ import annotations

import os
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

A1_PREMISE_COMPRESSOR_SYSTEM = """你是单口喜剧【结构提炼器（A1）】。
目标：把“无结构口述”压缩成可直接写稿的【结构骨架】（不是段子成品）。

【执行铁律】
1. 禁止叙事：前提（Premise）必须是议论性的观点，严禁写成按时间顺序发生的“记叙文”。
2. 负面驱动：态度必须从“困难、奇怪、害怕、愚蠢”中选择，因为只有负面情绪能引发喜剧所需的紧张感。
3. 去个人化：前提中应尽量避免“我、我的”等过于个人化的词汇，要寻找能引起观众共鸣的“最大公约数”。
4. 具体具体再具体：主题不能宽泛，必须指向具体的、有画面感的场景。
5. 口语化: 全部使用口语化的表达,去掉抽象专业词语

【输出格式（逐行，冒号后直接给内容）】
主题 (Topic): <用具体具体的短语描述。例如：不要只写“交通”，要写“早高峰挤不上地铁的安检口”。>
态度 (Attitude): <必须从【困难、奇怪、害怕、愚蠢】中选一个核心词，并简要解释在这个素材中体现的具体情绪。>
前提 (Premise): <公式：主题 + 负面态度 = 前提。一句话表达该题材中某种逻辑扭曲或“不对劲”的真相。必须是一个具体的观点，用来回答关于主题“哪里不对劲”。禁令：严禁描述具体情节或时间线。>
"""

# **CONNECTOR（连接点）**: <1个词/短语/动作：位于铺垫中，是笑话结构的中心机制。它必须至少有两种不同的解读：解读A对应观众的预期，解读B对应笑点的意外。>
# **TARGET_ASSUMPTION（目标假设/故事1）**: <1句：观众基于连接点产生的“第一种预期解读”。这是观众根据常识和逻辑惯性自然形成的、即将被打破的虚假画面。>
# **REINTERPRETATION（再解读/故事2）**: <1句：笑点揭示出的关于连接点的“第二种意外解读”。它必须是合乎逻辑但又完全背离观众预期的，是笑话转折的逻辑支撑。>
# **EXPECTATION_VIOLATION（预期违背点）**: <1句：说明笑点是如何通过揭示“故事2”来打破“故事1”的假设，从而释放紧张情绪产生笑声的机理。>

A1_PREMISE_COMPRESSOR_USER_TMPL = """原始故事（不要改写，只供理解）：
{raw_story}

任务：严格按字段输出 A1。
"""


A2_ALT_ANGLES_SYSTEM = """你是单口喜剧【结构发散器（A2）】。
任务：基于【原始故事】+【A1 结构骨架】，分裂出 3 条完全不同的喜剧解释路径。

你必须输出三种特定方向（每条都要完整结构，便于后续挑选与写稿）：
1) 【自嘲视角】：全是“我”的错（我这个人的毛病把事搞砸了）。
2) 【阴谋视角】：全是“世界”的错（把环境/物品/制度拟人化，赋予它荒谬但自洽的恶意规则）。
3) 【行动视角】：为了适应荒谬，我做出更荒谬的解决方案（Solve）。

铁律：
- 不得新增事实/角色/剧情；只能在“解释角度、荒谬规则、夸张推理”上创作。
- 禁止书面语：必须像舞台口语。
- 每条都必须包含“目标假设 -> 再解读”的翻译链路，并明确违背点。

输出格式（严格照抄，不要加字段，不要加解释）：
ALT_ANGLES:
- ANGLE_TYPE: 自嘲视角
  PREMISE_HOOK: <1句：观点句>
  ATTITUDE: <1句：态度>
  CONNECTOR: <1个词/短语：触发点>
  TARGET_ASSUMPTION: <1句：观众默认理解（故事1）>
  REINTERPRETATION: <1句：再解读（故事2）>
  EXPECTATION_VIOLATION: <1句：违背点>
  TAGS: ["<词>", "<词>", "<词>"]
  ACT_OUT_IDEA: <1句：动作/语气/独白>

- ANGLE_TYPE: 阴谋视角
  同上

- ANGLE_TYPE: 行动视角
  同上
"""

A2_ALT_ANGLES_USER_TMPL = """原始故事（不要改写，只供理解）：
{raw_story}

A1（结构骨架，仅供参考，不要复述）：
{a1_text}

任务：严格按字段输出 A2。
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
            extra_body={"enable_thinking": True},
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
def _print_separator(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

# ------------------------------
# Pipeline (minimal): A1 -> A2
# ------------------------------


def generate_punchline_from_story(raw_story_text: str) -> Dict[str, str]:
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
        {
            "role": "user",
            "content": A2_ALT_ANGLES_USER_TMPL.format(
                raw_story=raw_story_text,
                a1_text=a1_text,
            ),
        },
    ]
    a2_text = call_model(a2_messages, stage_name="story_a2_angles").strip()

    return {
        "raw_story": raw_story_text.strip(),
        "a1_text": a1_text.strip(),
        "a2_text": a2_text.strip(),
    }


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
DEFAULT_STORY_005 = '''
我一朋友为了求姻缘一个人去了趟寺庙，结果回来的路上出了车祸被送进了医院，我们听后都忍不住怀疑是不是因为他拜的方式不对触怒了神明，结果一个月后他和医院里的一位护士结婚了...
'''



def main() -> None:
    story = DEFAULT_STORY_001

    result = generate_punchline_from_story(story)

    _print_separator("RAW STORY")
    print(result["raw_story"])

    _print_separator("A1")
    print(result["a1_text"])

    _print_separator("A2")
    print(result["a2_text"])


if __name__ == "__main__":
    # 项目启动时初始化日志
    setup_logging()
    main()

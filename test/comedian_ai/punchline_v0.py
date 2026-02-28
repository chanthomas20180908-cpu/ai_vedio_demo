"""test/comedian_ai/punchline_v0.py

MVP punchline generator (standalone, non-core, non-mix-locked).

- Input: a case dict (topic, attitude, premises)
- Output: final joke text
- Design goals:
  1) Jump out of existing core/mix structure
  2) Keep code extremely small
  3) Preserve observability (print + logger) so you can see each step

NOTE: You must wire `call_model()` yourself to your deepseek-v3.2 calling code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

from dotenv import load_dotenv

from component.chat.chat import chat_with_model

# ------------------------------
# Prompts (MVP)
# ------------------------------

CALL1_SYSTEM = """你是中文单口喜剧写稿助手。目标：把生活素材写成“可上台”的短段子逐字稿。
核心要求：
- 不要写成故事流水账，要先给出一句清晰的【中心前提】（议论文观点）。
- 段子要口语化、具体、有画面，有1-2处对话即可。
- 禁止网络烂梗/谐音梗/鸡汤总结。
- 结尾一句必须是包袱（“底”），底后不要再解释。
- 保持“我”的非英雄视角：我在现场又气又无奈。
"""

CALL1_USER_TMPL = """输入信息：
- 主题：{topic}
- 态度：{attitude}
- 证据细节（请只用这些细节，不要扩写新剧情）：
1) {e1}
2) {e2}
3) {e3}

任务：请用三种不同“写法”各写一条候选段子，然后你自己选出最好的一条作为主推稿。
三种写法：
A【观察共鸣】抓一个细节反复放大，让观众“认出来就笑”。
B【预期违背】从以下方法中任选其一并标注：反转 / 三步定律 / 简单真相 / 自相矛盾 / 对比。
C【解决（绵里藏针）】给一个天才式回击/反问/操作，但要无伤大雅、不要威胁恐吓。

输出必须严格按这个格式：
CORE_PREMISE: <一句话>
A: <段子文本>
B: <段子文本> (METHOD=<你选的预期违背方法>)
C: <段子文本>
PICK: <A或B或C>
PICK_REASON: <不超过2句>
"""

CALL2_SYSTEM = """你是严苛的单口喜剧逐字稿编辑。
你只做“减法和锐化”：删废话、合并句子、把包袱的“底”放到最后。
禁止新增段落、禁止扩写新剧情、禁止换主题。
输出只给最终段子文本，不要任何说明。
"""

CALL2_USER_TMPL = """请把下面的段子编辑成可上台逐字稿：
硬要求：
- 只保留1-2处对话
- 总长度 160-220 字
- 最后一句必须是包袱（底在句末），底后不要再解释
- 不要网络梗/谐音梗/鸡汤
- 保持“我”的情绪：暴怒/无奈，但表达要干净利落

中心前提（不可丢）：{core_premise}

原稿：
{picked_text}
"""

# --- New: structure planning & draft writing (Call_A / Call_B) ---

STRUCTURE_SYSTEM = """你是单口喜剧结构规划助手。目标：基于素材先规划一份可读的段子结构，为后续写稿提供清晰骨架。
必须使用提供的 CASE_* 内容，不要扩写新剧情，不要杜撰人物。
输出格式（保持字段名）：
PREMISE: ...
DIMENSION: ...   # 语言/叙事/认知/社会
METHOD: ...      # 13种之一（任选其一并写出）
STORY1: ...
CONNECTOR: ...
STORY2: ...
EVIDENCE_PICK: [...3-5条你挑的细节...]
"""

STRUCTURE_USER_TMPL = """请基于以下素材先写“结构规划”，不要写成完整段子：
{e1}
{e2}
{e3}
"""

DRAFT_SYSTEM = """你是单口喜剧草稿写手。任务：仅根据给定的结构文本，写出一条 160-220 字、3-6 句、包袱在末尾的段子。
要求：口语化、有画面，禁止新增剧情或人物，禁止网络梗/谐音梗/鸡汤，底后不要再解释。
"""

DRAFT_USER_TMPL = """根据下面的结构写一条段子（直接输出段子文本，不要说明）：
{structure_text}
"""


# ------------------------------
# Case (embedded for zero deps)
# ------------------------------

CASE_1: Dict[str, Any] = {
    "name": "网约车司机迷路",
    "topic": "网约车司机迷路",
    "attitude": "愚蠢/暴怒",

    # 写作层（给模型“议论文骨架”）
    "core_premise": "我发现有些服务业的‘专业’，就是把责任外包给客户，还特别理直气壮。",
    "common_ground": "那种明明他在上班，但你像在给他交作业、还得保证他及格的憋屈感。",
    "target_assumption": "开网约车至少要能把导航当作最终裁判；如果还要问乘客，那我这单算我俩合伙开车。",
    "persona": "我也不是认路的人，但我被逼成了副驾教练+导航售后，边自嘲边暴怒。",
    "emotion_arc": [
        "一开始还想体谅：可能新手、不熟路，我就忍着提示两句。",
        "中段开始被迫上班：每个路口都要确认，我像在给他‘方向概念’补课。",
        "最后彻底爆炸：导航都到终点了，他还问‘我们在哪’，我意识到这不是迷路，是专业失能外包。",
    ],
    "connectors": [
        {
            "name": "方向/左右/往东",
            "meaning_A": "常识：往东就是地图上的东、左拐就是左边那条路。",
            "meaning_B": "歪解：方向不是常识，是需要乘客现场认证的选择题。",
        },
        {
            "name": "导航=权威",
            "meaning_A": "常识：导航说啥就照做，它是裁判。",
            "meaning_B": "歪解：导航只是背景音乐，真正的GPS是乘客的手指。",
        },
    ],
    "boundaries": "不写真实生死事故、不恐吓、不血腥；基调是无奈地笑。",
    "scene": {
        "time_hint": "像是晚高峰/车多路口多的时段（氛围：急）",
        "place_hint": "二环附近，路口密集，稍微走错就要绕圈",
        "my_state": "赶时间+已经上火，但还强装礼貌",
    },

    # 素材层（全量给模型：保留原9条 + 新增可演细节）
    "premises": [
        # 原始9条
        "司机明明开着导航，却不断问我路",
        "我说东二环，他问我东二环在哪个方向",
        "他瞪大眼睛看着导航屏幕，像在等包裹出生",
        "他问我：'东二环是往东还是往西？'",
        "我强忍着说：'师傅，东二环就是往东！'他接着问：'那往东是往哪边开？你给我指一下'",
        "我一边指路一边看着导航，感觉自己像给导航做人工售后",
        "每到一个路口，他都要灵魂发问：'左拐是左边这个吗？'",
        "他还安慰我：'别急别急，我对这附近不熟，慢慢找就熟了'",
        "最后导航说：'前方到达目的地'，他停下车问我：'那现在我们在哪儿？'",

        # 新增：更可演的对话/动作/节拍（不扩写新剧情，只补质感）
        "他问这些问题的时候语气特别认真，像在做安全培训：'确认一下哈。'",
        "我刚指完路，他立刻补一句：'你确定吗？'（那一瞬间我不知道谁是司机）",
        "导航提示音一响，他先不动，先看我，像在等我给导航盖章。",
        "每到路口他都会提前两秒踩刹车，然后扭头问：'这算路口吗？'",
        "我开始用手比划方向，手势越来越像机场地勤：左边！左边那条！",
        "我说'跟着导航走'，他回：'导航也会错啊，所以才问你。'（我当场被安排成二号导航）",
        "他还给我安慰：'别紧张，我们一起研究。'（这句话让我血压直接上二环）",
        "导航说'前方到达目的地'那一刻，他松了口气，好像是我终于把他送到了。",
    ],
}


# ------------------------------
# Logger (optional)
# ------------------------------

try:
    from config.logging_config import get_logger, setup_logging  # type: ignore

    logger = get_logger(__name__)
except Exception:  # pragma: no cover
    logger = None


def _log_info(msg: str) -> None:
    if logger is not None:
        logger.info(msg)


def _log_warn(msg: str) -> None:
    if logger is not None:
        logger.warning(msg)


def _log_debug(msg: str) -> None:
    if logger is not None:
        logger.debug(msg)


# ------------------------------
# Model call stub (YOU wire it)
# ------------------------------

def call_model(messages: List[Dict[str, str]], stage_name: str) -> str:
    """Wire this to your deepseek-v3.2 call.

    Expected:
      - messages: OpenAI-like chat messages
      - stage_name: used only for logging/debug

    Return:
      - assistant text content
    """
    # 加载API配置
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")
    # 调用AI
    try:
        # qwen
        # response = chat_with_model(
        #     api_key=self.api_key,
        #     model_type="qwen",
        #     model="qwen-max",
        #     messages=messages
        # )
        # deepseek
        response = chat_with_model(
            api_key=api_key,
            messages=messages,
            model_type="deepseek",
            model="deepseek-v3.2",
            extra_body={"enable_thinking": True},
        )

        logger.debug(f"📥 AI 响应长度: {len(response)} 字符")
        # self.logger.debug(f"📥 AI 响应内容:\n{response[:200]}...")  # 前200字符
        logger.debug(f"📥 AI 响应内容:\n{response}...")  # 前200字符

        return response

    except Exception as e:
        logger.error(f"❌ AI 调用失败: {e}")
        raise NotImplementedError("Please implement call_model() to invoke deepseek-v3.2 via your existing wrapper.")


# ------------------------------
# Evidence selection (local)
# ------------------------------

@dataclass
class ScoredPremise:
    premise: str
    score: int
    reasons: List[str]


def score_premise(p: str) -> ScoredPremise:
    score = 0
    reasons: List[str] = []

    if any(ch in p for ch in ["\"", "'", "“", "”"]):
        score += 5
        reasons.append("dialogue")

    if any(k in p for k in ["问", "说", "反问", "接着"]):
        score += 3
        reasons.append("ask/say")

    if any(k in p for k in ["盯", "瞪", "指", "停", "掀", "看"]):
        score += 2
        reasons.append("action")

    # tiny bump for concrete locational words (often helps premise specificity)
    if any(k in p for k in ["东", "西", "左", "右", "导航", "路口"]):
        score += 1
        reasons.append("concrete")

    return ScoredPremise(premise=p, score=score, reasons=reasons)


def select_top3_evidence(premises: List[str]) -> Tuple[List[str], List[ScoredPremise]]:
    """Legacy helper.

    Per latest direction, we do NOT use top-3 evidence selection to feed the LLM.
    We keep this scoring only for optional human visibility during debugging.
    """
    scored = [score_premise(p) for p in premises]
    scored_sorted = sorted(scored, key=lambda x: x.score, reverse=True)
    top = [s.premise for s in scored_sorted[:3]]
    return top, scored_sorted


def build_case_context_chunks(case: Dict[str, Any]) -> List[str]:
    """Build 3 chunks to keep CALL1 template unchanged (e1/e2/e3).

    We pass the FULL case to the LLM (no local selection/assessment).
    """
    meta_keys = [
        "name",
        "topic",
        "attitude",
        "core_premise",
        "common_ground",
        "target_assumption",
        "persona",
        "emotion_arc",
        "connectors",
        "boundaries",
        "scene",
    ]

    meta = {k: case.get(k) for k in meta_keys if k in case}
    premises = {"premises": case.get("premises", [])}

    chunk1 = "CASE_META_JSON:\n" + json.dumps(meta, ensure_ascii=False, indent=2)
    chunk2 = "CASE_PREMISES_JSON:\n" + json.dumps(premises, ensure_ascii=False, indent=2)
    chunk3 = "NOTE:\n请只使用以上 CASE_* 材料，不要扩写新剧情；可以夸张比喻，但不要引入生死事故/恐吓。"

    return [chunk1, chunk2, chunk3]


# ------------------------------
# Call1 parsing
# ------------------------------

@dataclass
class Call1Parsed:
    core_premise: str
    candidates: Dict[str, str]
    pick: str
    pick_reason: str


def parse_call1(text: str, topic: str, attitude: str) -> Call1Parsed:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    core_premise = ""
    candidates: Dict[str, str] = {}
    pick = ""
    pick_reason = ""

    for ln in lines:
        if ln.startswith("CORE_PREMISE:"):
            core_premise = ln.split(":", 1)[1].strip()
        elif ln.startswith("A:"):
            candidates["A"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("B:"):
            candidates["B"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("C:"):
            candidates["C"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("PICK:"):
            pick = ln.split(":", 1)[1].strip().upper()
        elif ln.startswith("PICK_REASON:"):
            pick_reason = ln.split(":", 1)[1].strip()

    # fallback
    if not core_premise:
        core_premise = f"我发现{topic}这种事，在{attitude}的时候特别离谱。"

    if pick not in {"A", "B", "C"}:
        pick = "A" if "A" in candidates else ("B" if "B" in candidates else ("C" if "C" in candidates else ""))

    if not candidates or not pick:
        # total parse failure
        raise ValueError("Call1 parse failed")

    return Call1Parsed(
        core_premise=core_premise,
        candidates=candidates,
        pick=pick,
        pick_reason=pick_reason,
    )


# ------------------------------
# Main generator
# ------------------------------

@dataclass
class PunchlineResult:
    evidence: List[str]
    scored_premises: List[ScoredPremise]
    call1_raw: str
    core_premise: str
    candidates: Dict[str, str]
    pick: str
    pick_reason: str
    picked_text: str
    structure_text: str
    draft_text: str
    call2_raw: str
    final_text: str


def generate_punchline_v0(case: Dict[str, Any]) -> PunchlineResult:
    topic = case["topic"]
    attitude = case["attitude"]
    premises: List[str] = case.get("premises", [])

    # Per latest direction: do NOT pick top-3 evidence to feed the LLM.
    # We still compute scoring for optional human debugging visibility.
    _, scored_sorted = select_top3_evidence(premises)

    evidence = build_case_context_chunks(case)

    _log_info(f"[punchline_v0] topic={topic} attitude={attitude} premises={len(premises)}")
    _log_info("[punchline_v0] feeding FULL case context to LLM (no local evidence selection)")

    # --- Call_A: structure planning ---
    structure_user = STRUCTURE_USER_TMPL.format(
        e1=evidence[0],
        e2=evidence[1],
        e3=evidence[2],
    )
    structure_messages = [
        {"role": "system", "content": STRUCTURE_SYSTEM},
        {"role": "user", "content": structure_user},
    ]
    structure_text = call_model(structure_messages, stage_name="punchline_v0_structure")

    # --- Call_B: draft writing based on structure ---
    draft_user = DRAFT_USER_TMPL.format(structure_text=structure_text)
    draft_messages = [
        {"role": "system", "content": DRAFT_SYSTEM},
        {"role": "user", "content": draft_user},
    ]
    draft_text = call_model(draft_messages, stage_name="punchline_v0_draft")

    # Compatibility placeholders for legacy fields
    call1_raw = structure_text
    core_premise = case.get("core_premise", f"我发现{topic}这种事，在{attitude}的时候特别离谱。")
    candidates: Dict[str, str] = {}
    pick = "STRUCTURE"
    pick_reason = ""
    picked_text = draft_text

    # --- Call_C: existing editing ---
    call2_user = CALL2_USER_TMPL.format(core_premise=core_premise, picked_text=picked_text)
    call2_messages = [
        {"role": "system", "content": CALL2_SYSTEM},
        {"role": "user", "content": call2_user},
    ]

    call2_raw = call_model(call2_messages, stage_name="punchline_v0_call2")
    final_text = call2_raw.strip()

    return PunchlineResult(
        evidence=evidence,
        scored_premises=scored_sorted,
        call1_raw=call1_raw,
        core_premise=core_premise,
        candidates=candidates,
        pick=pick,
        pick_reason=pick_reason,
        picked_text=picked_text,
        structure_text=structure_text,
        draft_text=draft_text,
        call2_raw=call2_raw,
        final_text=final_text,
    )


def _print_separator(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    case = CASE_1

    _print_separator("INPUT")
    print(f"name: {case.get('name')}")
    print(f"topic: {case['topic']}")
    print(f"attitude: {case['attitude']}")
    print(f"premises: {len(case['premises'])}")

    result = generate_punchline_v0(case)

    _print_separator("STEP0: INPUT CONTEXT (FULL CASE → LLM)")
    print("Call1 evidence chunks (e1/e2/e3):")
    for i, e in enumerate(result.evidence, 1):
        print(f"\n--- e{i} (len={len(e)}) ---")
        print(e)

    print("\nOptional scoring visibility (top 12 shown; NOT used for selection):")
    for s in result.scored_premises[:12]:
        rs = ",".join(s.reasons) if s.reasons else "-"
        print(f"  score={s.score:2d} reasons={rs:18s} premise={s.premise}")

    _print_separator("STRUCTURE RAW (Call_A)")
    print(result.structure_text)

    _print_separator("DRAFT RAW (Call_B)")
    print(result.draft_text)

    _print_separator("CALL2 INPUT")
    print(f"CORE_PREMISE (locked): {result.core_premise}")
    print("\nPICKED_TEXT:")
    print(result.picked_text)

    _print_separator("CALL2 OUTPUT (FINAL)")
    print(result.final_text)
    print("\nLENGTH:")
    print(f"picked={len(result.picked_text)} final={len(result.final_text)}")


if __name__ == "__main__":
    # 项目启动时初始化日志
    setup_logging()
    main()

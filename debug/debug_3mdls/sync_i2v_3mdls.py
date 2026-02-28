"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_sync_i2v_3mdls.py
"""

import os
import sys

# 让脚本在 debug/debug_3mdls/ 下也能 import 项目包
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.logging_config import get_logger, setup_logging
from debug.debug_sync_wan_i2v import debug_synx_i2v_wan22
from test.test_i2v_doubao import debug_seedance_i2v
from test.test_i2v_minimax import debug_minimax_i2v
from util.util_url import upload_file_to_oss

import time
from typing import Callable, Dict, List, Tuple, Optional


def debug_sync_i2v_mdls(
    image_path: str,
    prompt: str,
    enabled_models: Optional[List[str]] = None,
) -> List[Dict]:
    """
    同一张图、同一条 prompt，串行跑多种 I2V 模型。

    :param image_path: 本地图片路径
    :param prompt: 文本提示词
    :param enabled_models: 要运行的模型 name 列表（见下方 model_configs 里的 'name'）。
                           为 None 或空列表时，表示跑所有模型。
    :return: 每个模型的结果列表：
             [
               {
                 "model": "wan-2.2-i2v-plus",
                 "video_url": "...",
                 "video_path": "...",
                 "time_calculate": "0.1234 秒"
               },
               ...
             ]
    """
    logger = get_logger(__name__)

    # 统一上传一次图片，所有模型复用同一个 OSS URL
    image_url = upload_file_to_oss(image_path, 300)

    video_list: List[Dict] = []

    # 定义各模型的调用配置
    model_configs: List[Dict] = [
        {
            "name": "wan-2.2-i2v-plus",
            "label": "wan 2.2 i2v",
            "timed": True,
            "run": lambda url, p: debug_synx_i2v_wan22(url, p),
        },
        {
            "name": "doubao-seedance-1-lite",
            "label": "seedance 1 lite i2v",
            "timed": True,
            "run": lambda url, p: debug_seedance_i2v(url, p, "lite"),
        },
        {
            "name": "doubao-seedance-1-pro",
            "label": "seedance 1 pro i2v",
            "timed": True,
            "run": lambda url, p: debug_seedance_i2v(url, p, "pro"),
        },
        {
            "name": "MiniMax-Hailuo-02",
            "label": "minimax i2v",
            "timed": True,
            "run": lambda url, p: debug_minimax_i2v(url, p),
        },
    ]

    # 如果传入了 enabled_models，就转成 set，方便判断
    enabled_set = set(enabled_models) if enabled_models else None

    for cfg in model_configs:
        name = cfg["name"]

        # 开关控制：如果配置了 enabled_models 且当前模型不在里面，就跳过
        if enabled_set is not None and name not in enabled_set:
            logger.info(f"跳过模型 {name}（不在 enabled_models 中）")
            continue

        label = cfg["label"]
        timed = cfg.get("timed", False)
        run_fn: Callable[[str, str], Tuple[str, str]] = cfg["run"]

        logger.info(f"----- {label} -----")
        start_time = time.time()

        video_url = None
        video_path = None
        try:
            result = run_fn(image_url, prompt)
            if isinstance(result, tuple) and len(result) == 2:
                video_url, video_path = result
            elif result is None:
                logger.warning(f"{label} 返回 None（可能被风控/任务失败），跳过")
            else:
                logger.warning(f"{label} 返回非预期结果类型: {type(result)}，跳过")
        except Exception as e:
            logger.exception(f"{label} 运行异常，跳过: {e}")

        end_time = time.time()
        time_cal = f"{end_time - start_time:.4f} 秒"

        if timed:
            logger.info(f"{label} 运行时间: {time_cal}")

        record: Dict = {
            "model": name,
            "video_url": video_url,
            "video_path": video_path,
        }
        if timed:
            record["time_calculate"] = time_cal

        video_list.append(record)

    return video_list


if __name__ == "__main__":
    setup_logging()

    # 记录开始时间
    start_time = time.time()

    IMAGE_PATH = "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/一比一角色形象图/NBA/download_kobe_001.png"

    # 仅使用你确认的 3 个模型
    ENABLED_MODELS = [
        "wan-2.2-i2v-plus",
        "doubao-seedance-1-lite",
        "MiniMax-Hailuo-02",
    ]

    PROMPT_MILITARY_SALUTE = r'''{
  "主题": "保安室上岗：突然军姿敬礼到离谱",
  "人物": {
    "外貌": "严格保持上传图片角色外貌一致性（性别、五官、肤色、发型、气质不变）。在不改变脸部与发型的前提下，整体风格变为保安上岗风格，服装完整不消失、不裸露、不变形为不合理造型。",
    "表情": "从平静到毫无预兆的‘极端严肃’（眼睛睁大、嘴角强行抿直），再到反常得意的微笑，喜剧来自过度认真。",
    "动作": [
      {
        "阶段": "上岗站姿",
        "描述": "角色站在画面中央，双脚站稳，双手自然在身体两侧，表情平静看向镜头。"
      },
      {
        "阶段": "突然立正（极快极大）",
        "描述": "毫无预兆地‘啪’一下站得极其笔直：背挺直、胸口打开、下巴微抬；双手迅速贴裤缝，动作突然且幅度大。"
      },
      {
        "阶段": "夸张敬礼（僵住）",
        "描述": "右手猛地抬起敬礼，速度快、幅度大；敬礼后整个人僵住0.5秒不动，眼神死死盯镜头，严肃到荒诞。"
      },
      {
        "阶段": "正步两下（抬腿高）",
        "描述": "角色原地正步踏两下，抬腿更高更标准，动作突然且夸张；上半身保持笔直。"
      },
      {
        "阶段": "反常收尾",
        "描述": "角色突然放松，肩膀一垮，嘴角诡异上扬露出‘我超专业’的得意笑，然后快速点头两下。"
      }
    ]
  },
  "背景": {
    "变化": "场景明确变为值班室：狭小值班室空间，桌面与多屏幕墙（屏幕内容为模糊画面块，不出现可读文字），室内日光灯与简洁值班氛围。",
    "连贯性": "全程保持值班室场景不变化、不切回。"
  },
  "特效": {
    "描述": "不使用炫光与粒子；仅允许在‘突然立正’瞬间出现极轻微镜头震动，强调突然性。",
    "风格": "简单真实，笑点靠动作和神态反常。"
  },
  "镜头": {
    "构图": "中景或中近景，保证能看到上半身与正步抬腿动作，脸部清晰。",
    "动态": "镜头机位稳定，动作幅度大但人物不出框。"
  },
  "时长": "5s",
  "时序逻辑": {
    "0.00s-1.10s": "上岗站姿：平静看镜头。",
    "1.10s-2.10s": "突然立正+夸张敬礼并僵住。",
    "2.10s-3.20s": "正步两下（抬腿高）。",
    "3.20s-5.00s": "反常收尾：肩垮+得意笑+快速点头两下。"
  },
  "遮挡与安全区": {
    "面部安全区定义": "双眼、鼻梁、嘴部与面部轮廓必须全程清晰可见。",
    "轨迹限制": "敬礼手掌靠近额头但避免遮挡眼睛与鼻梁正前。",
    "特效叠加限制": "不使用漂浮物、文字、粒子。"
  }
}'''

    PROMPT_RUNWAY_A = r'''{
  "主题": "霓虹T台升起：妩媚走秀A（媚但克制）",
  "人物": {
    "外貌": "严格保持上传图片角色外貌一致性；脸与发型不变；衣物保持完整不消失、不裸露，不出现衣物突然消失或断裂。",
    "表情": "普通平静→突然反常自信妩媚（轻眯眼+挑眉）→夸张满意→最后突然一本正经装没事（反差笑点）。",
    "动作": [
      {
        "阶段": "T台启动（突然）",
        "描述": "角色毫无预兆肩膀一扭、重心一移，腰胯明显摆动但克制；同时脚下出现并升起一条窄长T台，角色随T台升起仍保持平衡。"
      },
      {
        "阶段": "大步走秀两步（卡点）",
        "描述": "角色在T台上走两步：步幅大、节奏突然、每一步有明显停顿卡点；手臂摆动克制但姿态很‘装’。"
      },
      {
        "阶段": "半圈转身+反常眨眼挑眉",
        "描述": "角色原地半圈转身再面向镜头，做一个反常夸张的眨眼挑眉，嘴角微翘。动作突然、幅度明显但不低俗。"
      },
      {
        "阶段": "POSE两连（突然切换）",
        "描述": "快速切两个POSE：一手叉腰定住0.3秒→立刻切到更挺胸抬下巴的定格POSE，表情夸张满意。手势不抬到脸前。"
      },
      {
        "阶段": "突然装没事",
        "描述": "角色瞬间恢复严肃平静表情，站姿正常，像刚才什么都没发生。"
      }
    ]
  },
  "背景": {
    "变化": "场景明确变为霓虹灯秀场：后方霓虹灯墙与简洁舞台结构，地面为窄长T台延伸到远处，环境有舞台空间感但不出现文字标语。",
    "连贯性": "全程保持霓虹T台秀场不变化、不切回。"
  },
  "服装": {
    "变化": "衣物保持完整不消失；仅允许衣服质感更利落挺括、更‘秀场高级’，但不能变成不合理造型。",
    "连贯性": "服装变化轻微自然，脸与发型绝不变化。"
  },
  "特效": {
    "描述": "不使用粒子或炫光爆炸；霓虹灯作为背景场景元素，保持简洁不过度闪烁。",
    "风格": "清晰场景+夸张动作取笑点。"
  },
  "镜头": {
    "构图": "中景偏中近景，确保能看到T台升起与走秀步伐，脸部清晰。",
    "动态": "镜头基本固定，主要冲击来自T台升起与动作突然性。"
  },
  "时长": "5s",
  "时序逻辑": {
    "0.00s-1.40s": "T台启动：T台出现并升起，角色肩扭胯摆突然妩媚。",
    "1.40s-2.80s": "走秀两步（卡点明显）。",
    "2.80s-3.60s": "半圈转身+眨眼挑眉。",
    "3.60s-4.60s": "POSE两连突然切换。",
    "4.60s-5.00s": "突然装没事定格。"
  },
  "遮挡与安全区": {
    "面部安全区定义": "面部全程清晰可见。",
    "轨迹限制": "手势在下巴以下完成，不遮挡眼睛与鼻梁正前。",
    "特效叠加限制": "不使用漂浮物、文字、粒子。"
  }
}'''

    PROMPT_DEEP_BOW = r'''{
  "主题": "礼堂舞台：礼貌过头的鞠躬连击",
  "人物": {
    "外貌": "严格保持上传图片角色外貌一致性；不新增明显道具配饰。",
    "表情": "职业微笑→突然过度严肃真诚→抬头尴尬但还要礼貌→反常快速点头圆场。",
    "动作": [
      {
        "阶段": "点名站直",
        "描述": "角色突然站直，表情瞬间严肃，像被点名上台，眼神过度认真看说向镜头。"
      },
      {
        "阶段": "猛折超大鞠躬（极夸张）",
        "描述": "毫无预兆猛地鞠躬到接近90度甚至更低，动作快且幅度巨大，像上半身被瞬间折下去。"
      },
      {
        "阶段": "低位僵住停顿（荒诞）",
        "描述": "保持低位鞠躬僵住0.6秒完全不动。"
      },
      {
        "阶段": "二连更狠",
        "描述": "抬起一点点后立刻再来一次更快更低的鞠躬，再僵住0.3秒。"
      },
      {
        "阶段": "三连小补刀",
        "描述": "突然补一个短促小鞠躬（速度极快像抽动），然后马上停住。"
      },
      {
        "阶段": "尴尬抬头圆场",
        "描述": "慢慢抬头回正，尴尬但礼貌地笑；眼神躲闪一下又赶紧看回镜头，最后反常快速点头两下结束。"
      }
    ]
  },
  "背景": {
    "变化": "场景明确变为礼堂舞台或颁奖典礼：身后是舞台幕布/背景板与台阶结构，地面为舞台地板，空间开阔，有典礼氛围但不出现文字标语。",
    "连贯性": "全程保持礼堂舞台场景不变化、不切回。"
  },
  "特效": {
    "描述": "不使用炫光粒子；仅允许第一次猛折瞬间极轻微镜头震动强调冲击。",
    "风格": "简洁，笑点靠鞠躬连击的荒诞。"
  },
  "镜头": {
    "构图": "中景，保证鞠躬幅度巨大时上半身仍在画面内；抬头时脸回到画面中心清晰。",
    "动态": "镜头机位稳定，避免跟随过度造成眩晕。"
  },
  "时长": "5s",
  "时序逻辑": {
    "0.00s-0.70s": "点名站直：过度认真。",
    "0.70s-1.50s": "猛折超大鞠躬。",
    "1.50s-2.10s": "低位僵住停顿。",
    "2.10s-3.20s": "二连更狠（更快更低）+短僵住。",
    "3.20s-3.60s": "三连小补刀（短促）。",
    "3.60s-5.00s": "尴尬抬头圆场+反常快速点头两下。"
  },
  "遮挡与安全区": {
    "面部安全区定义": "抬头阶段面部必须清晰可见。",
    "轨迹限制": "双手始终在身体前侧或下方，不抬到脸前。",
    "特效叠加限制": "不使用漂浮物、文字、粒子。"
  }
}'''

    TASKS = [
        {
            "title": "保安室-军姿-敬礼-正步",
            "image_path": IMAGE_PATH,
            "prompt": PROMPT_MILITARY_SALUTE,
            "enabled_models": ENABLED_MODELS,
        },
        {
            "title": "霓虹T台升起-妩媚走秀A",
            "image_path": IMAGE_PATH,
            "prompt": PROMPT_RUNWAY_A,
            "enabled_models": ENABLED_MODELS,
        },
        {
            "title": "礼堂舞台-鞠躬连击",
            "image_path": IMAGE_PATH,
            "prompt": PROMPT_DEEP_BOW,
            "enabled_models": ENABLED_MODELS,
        },
    ]

    for idx, task in enumerate(TASKS, start=1):
        results = debug_sync_i2v_mdls(
            image_path=task["image_path"],
            prompt=task["prompt"],
            enabled_models=task["enabled_models"],
        )

        print(f"--- 结果 ({idx}/{len(TASKS)}) {task['title']} ---")
        for result in results:
            print(f"模型: {result['model']}")
            print(f"视频URL: {result['video_url']}")
            print(f"视频路径: {result['video_path']}")
            if "time_calculate" in result:
                print(f"耗时: {result['time_calculate']}")
            print("-" * 40)

    # 记录结束时间并计算运行时间
    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")

"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_audio_sync.py
"""

import os
import time

from dotenv import load_dotenv

from component.muti.synthesis_audio import synthesis_audio
from config.logging_config import setup_logging


def debug_sync_audio(_api_key, _text ,_voice_id):
    # 调用通用音频合成函数
    save_path, _, log_info = synthesis_audio(
        api_key=_api_key,
        model_type="cosyvoice",
        text=_text,
        voice=_voice_id,
    )

    return save_path


if __name__ == "__main__":
    setup_logging()

    # logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))

    # 测试Qwen模型
    api_key = os.getenv("DASHSCOPE_API_KEY")
    # dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    # 记录开始时间
    start_time = time.time()

    # 调用函数
    # user_input = '圣诞节的表情包'
    text= '''
我觉得，我对自己要求有点太高了。连情绪管理，都想做到尽善尽美。

昨晚在楼道里崩溃大哭，但我没法专心。因为环境不完美……灯，灭了。

我需要一个完整的氛围，有灯光配合，才算哭得“标准”。我内心那个完美主义监工，它根本不在乎我为什么哭，只在乎我的哭相，在灯光下是否合格。

所以，它给我的 KPI 就是：哭满三十秒。必须跺脚亮灯。检查一下……演出效果。

我怀疑那个监工，可能是我前老板转世来的。

……但你知道吗？我哭得那么投入，还以为自己挺惨。可那盏灯，可能有它的“高级视角”。它每天听那么多“回家”、“外卖”的脚步声，早腻了。

它现在想收集点特别的，比如……人类崩溃的音频样本。

它可能在想：“今天收了三个‘失恋型’，一个‘工作压力型’……你这个，‘自怨自艾间歇型’？新品种。录了。”

但它好像对我不太满意，所以故意灭灯。意思是：“刚才那段感情不够饱满。重来！跺脚给我加点节奏感。”

于是，我就真成了一个按指令表演的“声控哭偶”。我以为我在发泄，其实是在给一盏高级灯……交作业。

这导致我为了完成这场 KPI 崩溃，被迫开发出了一套精准系统。我发现，完美崩溃只需要三步：

第一步：沉浸。允许自己哭出来……呜——

第二步：分心。开始倒计时……28……29……

第三步：执行！时间到！立刻暂停所有悲伤，调用腿部肌肉，完成一次愤怒的跺脚！

现在我这个流程熟练到，我悲伤时喘气，都带着预备跺脚的节奏。

我的人生新准则：任何情绪，都能在三十秒内，分解成可执行的……三个步骤。    '''
    res = debug_sync_audio(api_key, text, "longhouge")

    print( res)

    # 记录结束时间并计算运行时间
    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")

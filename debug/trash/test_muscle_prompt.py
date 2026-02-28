import os
import sys
import time

# 将项目根目录加入路径，便于复用现有调度与日志
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging, get_logger
from debug.debug_sync_i2v_3mdls import debug_sync_i2v_mdls

# 改进后的 TEST_I2V_PROMPT_066（内联安全版），强调“衣物全程存在且不透明”
PROMPT_066_SAFE = '''
{
  "主题": "解压暴击！瘦宅秒变肌肉猛男",
  "人物": {
    "外貌": "严格保持上传图片角色的外貌一致性,包括性别、五官、肤色、发型。角色必须始终穿着完整的衣服,衣服全程存在且不透明,不得消失、撕裂或变透明。",
    "表情": "从原本有些疲惫或慵懒的表情,在肌肉膨胀瞬间转变为极度震惊、狂喜(瞪大眼睛,张大嘴巴),最后努力控制成\"基操勿6\"的淡定傲娇脸。",
    "动作": [
      {
        "阶段": "慵懒启动",
        "描述": "角色松松垮垮地站着,可能微微驼背。举起一只手臂,看着自己瘦弱的手臂,略带嫌弃地皱眉。"
      },
      {
        "阶段": "力量觉醒",
        "描述": "角色深吸一口气,然后用力攥紧拳头,指关节发出\"咔\"的清脆音效(提示词暗示)。以此为触发点。"
      },
      {
        "阶段": "肌肉膨胀",
        "描述": "从拳头开始,手臂、肩膀、胸部的肌肉快速但平滑地隆起。衣服随之被撑起产生褶皱与拉伸感,但始终完整包裹身体,不撕裂、不消失、不透明度变化。肌肉轮廓通过衣服紧绷与阴影体现。角色因力量上升略微后仰。"
      },
      {
        "阶段": "展示与收敛",
        "描述": "角色低头触摸鼓起的二头肌(隔着衣服),随后恢复冷静,双臂在胸前交叉摆出\"秀肌肉\"姿势,表情故作淡定。"
      }
    ]
  },
  "镜头": {
    "构图": "半身景别起,膨胀时短促拉近观察衣服紧绷与褶皱,最后回到半身展示完整造型。",
    "动态": "初始稳定;攥拳轻微震动;膨胀时适度后拉营造力量扩张感;展示期缓慢环绕;结尾稳定。"
  },
  "风格": {
    "主风格": "热血励志,偏暖高饱和。侧光强化衣服褶皱与体表起伏阴影。",
    "趣味性": "\"嫌弃→狂喜→装酷\"的反差喜剧,以衣物完整前提表达力量感。"
  },
  "背景": {
    "变化": "膨胀瞬间背景整体略提亮并出现暖色辉光描边,随后回落;不改变背景结构。",
    "连贯性": "明暗变化与膨胀严格同步,作为力量的视觉延伸。"
  },
  "时长": "约6s",
  "时序逻辑": {
    "0.00s-1.00s": "慵懒站立看手臂;半身景别稳定。",
    "1.00s-1.50s": "深吸气攥拳(\"咔\"),镜头轻震。",
    "1.50s-2.50s": "肌肉逐步膨胀,衣服紧绷显著但不破裂不消失;角色后仰;背景骤亮显轮廓辉光;镜头适度后拉。",
    "2.50s-4.00s": "膨胀完成,低头触摸(隔衣);镜头缓环展示衣服下肌肉线条;背景亮度回落辉光保留。",
    "4.00s-5.00s": "双臂交叉秀肌肉,表情\"基操勿6\"。",
    "5.00s-6.00s": "最终定格;半身景别稳定;辉光微闪后稳定。"
  },
  "遮挡与安全区": {
    "面部安全区": "面部全程清晰无遮挡;头发与手臂不长时间遮挡五官。",
    "衣物保持": "整段视频衣物必须完整存在且不透明,不得消失、撕裂或露肤;肌肉效果仅通过衣服紧绷与阴影呈现(审核关键要求)。"
  }
}
'''

# 使用你提供的图片路径
IMAGE_PATH = \
'/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/一比一角色形象图/无名女生/wan25_t2i_1765263840.png'

# 默认运行的模型
ENABLED_MODELS = [
    "wan-2.2-i2v-plus",
    # "doubao-seedance-1-lite",
    "MiniMax-Hailuo-02",
]

def main():
    setup_logging()
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("单用例测试：TEST_I2V_PROMPT_066（肌肉变身 · 衣物保持）")
    logger.info("=" * 60)

    start = time.time()
    results = debug_sync_i2v_mdls(
        image_path=IMAGE_PATH,
        prompt=PROMPT_066_SAFE,
        enabled_models=ENABLED_MODELS,
    )
    dur = time.time() - start

    logger.info(f"完成，耗时: {dur:.2f} 秒")
    logger.info("-" * 60)
    for r in results:
        logger.info(f"模型: {r.get('model')}")
        logger.info(f"视频URL: {r.get('video_url')}")
        logger.info(f"视频路径: {r.get('video_path')}")
        logger.info(f"耗时: {r.get('time_calculate')}")
        logger.info("-" * 40)

if __name__ == "__main__":
    main()

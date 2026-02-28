#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""IDE-friendly debug runner for wan2.6-image (HTTP sync).

直接在 IDE 里修改下面的常量，然后点 Run。

规则：
- IMAGE_PATHS 仅支持本地路径（1~4）
- 默认输出目录：config.PICTURE_RESULTS_DIR
"""

from pathlib import Path
import sys

# Ensure pythonProject/ is on sys.path so `component.*` imports work when running from debug/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from component.muti.wan26_image_sync import wan26_generate


# =====================
# Edit these in IDE
# =====================
PROMPT = (
'''
基于上传图片人物的身份一致性与“摊手”动作语义，但画面必须像史诗魔幻电影海报：强烈陌生感、强戏剧性重构，而不是原图裁切或轻度调色。主体必须是“真人”，绝对不要生成雕像、石像、纪念碑质感。

【核心意象（动作的升级）】
把“经典摊手”升级为“俯瞰众生的神性展开双臂”意象（参考里约山巅展开双臂的视觉符号，但不要出现雕像、不要宗教图腾、不要十字架、不要圣像化装置）。动作仍然是：双臂外展、手心向上、耸肩，但姿态更宏大、更像在风暴中宣告与辩白。

【整体风格】
史诗魔幻黑暗电影感（epic fantasy + cinematic noir）。黑位压实（crushed blacks），高对比（high contrast），强烈暗角（heavy vignetting），35mm 电影颗粒，局部高光如刀锋。

【场景（必须特别、陌生、宏大）】
夜色山巅的“风暴王座”场景：人物站在悬崖/山脊边缘，脚下是湿润黑岩与薄雾，远处是巨大的云海与城市灯火像星河铺开（不是篮球场、不是普通看台）。乌云翻滚，闪电只做远处天幕轮廓（不要照亮全画面），云雾与尘埃被一道天光切开形成体积光柱，空间感巨大、压迫、神话史诗。

【主体与表情（更夸张戏剧化）】
角色居中，占画面 70% 左右，真人皮肤与球衣材质真实。摊手动作要夸张定格：肩更耸、手心更外翻、身体微前倾，像在风暴与命运面前“无奈 + 抱怨 + 自我辩解式推诿”。表情强烈：眉更紧、嘴角更压、眼神更锋利更委屈，像在对天地控诉。

【镜头语言】
超低机位轻仰拍（low angle），24mm 广角电影镜头，轻微透视畸变；背景极虚但保留云海与城市灯火的尺度。允许前景有少量模糊黑影/飞散雨雾增强压迫感，但不得遮挡面部。

【布光（必须更暗）】
单一强聚光天光（single hard top spotlight）从上方打下切割面部与肩线；冷色侧逆光勾勒轮廓。禁止均匀补光、禁止整体泛亮、禁止平光手机照。

【硬性约束】
不要裁判；不要篮球场实况转播感；不要雕像/石像/纪念碑/石材皮肤；不要宗教符号（十字架、圣光环、圣像）；不要字幕/水印/文字；不要卡通；不要新增清晰人物抢戏；画面必须更暗、更电影、更陌生、更震撼。
'''
)
IMAGE_PATHS = [
    "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/下载原图/老詹/小手一摊.jpeg",
]
SIZE = "1024*1024"
N = 1
NEGATIVE_PROMPT = (
    "海报文字, 标题文字, 字幕, 排版文字, 水印, 新增文字, 可读文字, 额外字母, 额外数字, "
    "低质量, 模糊, 过曝, 过度锐化, 塑料质感, "
    "整体过亮, 发灰, 均匀补光, 曝光抬高, 平光, 旅游照, 手机随手拍, 过度保真, 看起来像原图裁切, 缺乏戏剧光影, 缺乏电影调色"
)
LOCK_SUBJECT = True
OSS_TTL = 300

def main() -> int:
    paths, urls, request_id = wan26_generate(
        prompt=PROMPT,
        image_paths=IMAGE_PATHS,
        size=SIZE,
        n=N,
        negative_prompt=NEGATIVE_PROMPT,
        lock_subject=LOCK_SUBJECT,
        oss_ttl=OSS_TTL,
        # save_dir=SAVE_DIR,
    )

    print("request_id:", request_id)
    print("saved:")
    for p in paths:
        print(" ", p)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

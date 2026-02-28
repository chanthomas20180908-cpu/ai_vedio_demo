# for the nano banana pro, dark style
t2i_prompt_dark_style = """
{
  "style_guide": {
    "core_aesthetic": "DC电影暗黑宇宙风格 (DC Dark Universe) / 《新蝙蝠侠》(The Batman 2022) 视觉美学。",
    "visual_references": [
      "光影参考：格雷格·弗莱瑟 (Greig Fraser) 的摄影风格——在绝对的黑暗中只用一束光切割物体。",
      "色调参考：'死黑' (Crushed Blacks) + '脏旧的琥珀色' (Dirty Amber) + '高对比度'。"
    ],
    "look_keywords": [
        "电影黑色风格 (Cinematic Noir)",
        "粗野主义史诗 (Brutalist Epic)",
        "压迫性氛围",
        "曝光不足 (Underexposed)",
        "死黑/暗部压暗 (Crushed Blacks)",
        "高对比度",
        "选择性高光",
        "35mm 胶片颗粒",
        "体积雾 + 尘埃 (Volumetric Fog)",
        "夸张叙事",
        "反直觉",
        "戏剧化"
      ]
    "darkness_level": "极度欠曝 (Underexposed)。画面80%应该是纯黑色或深灰色阴影，只有主体轮廓可见。"
  },
  "subject": {
    "character": "写实的NBA巨星（面部保留原图特征），摊手表示不满,总认为事情应该朝着利于他的方向发展,显得可笑之极。",
    "wardrobe_highlight": "摊手,咆哮,索要更多的东西,贪得无厌,软蛋",
    "pose": "像大猩猩一样狂野,摊手,",
    "background": "站在球场上,但是马上就要输了,身边都是可以打爆他的球员和人,冷酷地看着他 。身边是裁判,像是大猩猩饲养员一样看着他",
    "vibe": "冷酷、沉默、极度危险的放松感。"
  },
  "technical_specs": {
    "lighting": "顶光 (Top Light) + 轮廓光 (Rim Light)。面部一半在阴影中（伦勃朗光）。",
    "camera": "IMAX 广角镜头，低机位仰拍，极远景构图。",
  },
  "negative_constraints": [
    "禁止文字 (No Text)",
    "禁止商标 (No Logos)",
    "禁止明亮环境 (No Brightness)",
    "禁止卡通感 (No Cartoon)",
    "禁止看起来像普通照片 (Not a snapshot)"
  ]
}
"""
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_image_sync_from_image.py
"""

from component.chat.chat import chat_with_model
from component.muti.synthesis_image import sync_i2i_wan_v25, sync_t2i_wan_v25
from component.muti.synthesis_picture import synthesis_picture_with_qwen, synthesis_picture_with_wan
from component.muti.visual_understanding import understand_image
from config.logging_config import get_logger
from config import config as cfg
from config import prompt_default as prompt
from util.util_url import upload_file_to_oss
from dashscope import ImageSynthesis

logger = get_logger(__name__)


def image_sync_from_images8subtitle_with_text2image(api_key, image_path_list, subtitle, instruction):
    """
    通过提取图片信息和字幕信息，用文生图重新生成图片
    """

    # 生成图片url
    image_url_list = [upload_file_to_oss(image_path, 300) for image_path in image_path_list]

    # 理解图片信息 - 使用统一配置的提示词
    image_info_list = []  # 只包含图片理解信息的list
    image_url_info_list = []  # 包含图片url和图片信息的dict的list

    for image_url in image_url_list:
        # 理解单张图片
        image_info = understand_image(
            api_key,
            image_url,
            prompt.IMAGE_UNDERSTANDING_PROMPT.substitute(instruction=instruction),
        )

        # 添加到只包含图片信息的列表
        image_info_list.append(image_info)

        # 添加到包含url和信息的字典列表
        image_url_info_list.append({
            "url": image_url,
            "info": image_info
        })

    print(f"图片结构化信息：\n{image_info_list}\n")
    print(f"图片URL和信息：\n{image_url_info_list}\n")

    # # 理解字幕信息
    # messages = [
    #     {
    #         "role": "system",
    #         "content": prompt.SUBTITLE_UNDERSTANDING_PROMPT_SYSTEM_TEMPLATE.substitute(),
    #     },
    #     {
    #         "role": "user",
    #         "content": prompt.SUBTITLE_UNDERSTANDING_PROMPT_USER_TEMPLATE.substitute(instruction=instruction, subtitle=subtitle),
    #     }
    # ]
    # print(f"开始字幕理解，massages:\n{messages}\n")
    # subtitle_info = chat_with_model(api_key=api_key, model_type="qwen", model="qwen-max", messages=messages)
    # print(f"字幕结构化信息：\n{subtitle_info}\n")

    subtitle_info = '''
    字幕结构化信息：
    ```json
    {
      "Theme": {
        "MainIdea": "搞笑",
        "Emotion": "欢乐"
      },
      "Setting": {
        "Time": "现代",
        "Location": "厨房（模仿地狱厨房的综艺节目现场）"
      },
      "Plot": {
        "Hook": "六位来自全球的新厨师将面临一个前所未有的挑战：烹饪一只已经灭绝了6500万年的霸王龙。",
        "Conflict": "厨师们需要在极端的压力下处理一个极其不寻常且荒谬的任务，即烹饪一只大型霸王龙。",
        "Climax": "主持人用夸张的语言和比喻来批评厨师们的表现，比如“这扇贝太生了，我还能听到它叫海绵宝宝滚开”等，制造出紧张而幽默的气氛。",
        "Resolution": "视频以主持人的命令“出去！出去！”结束，暗示着至少一位厨师可能因为表现不佳而被淘汰。但整个过程是以一种轻松、戏谑的方式呈现的，强调娱乐性而非严肃的竞争结果。"
      },
      "Purpose": {
        "Message": "通过模仿著名烹饪节目《地狱厨房》的形式，并加入超现实元素如烹饪恐龙，旨在为观众提供一种新颖独特的娱乐体验，同时保持对原版节目的敬意。",
        "CallToAction": "虽然没有明确提到具体的行动号召，但这种类型的搞笑视频通常鼓励观众点赞、分享以及关注创作者频道，以便获得更多类似内容。"
      }
    }
    ```
    '''

    # 综合多图信息和字幕信息，生成故事摘要
    messages = [
        {
            "role": "system",
            "content": prompt.STORY_ABSTRACT_SYNC_PROMPT_SYSTEM_TEMPLATE.substitute(),
        },
        {
            "role": "user",
            "content": prompt.STORY_ABSTRACT_SYNC_PROMPT_USER_TEMPLATE.substitute(instruction=instruction, images_info=image_info_list, subtitle_info=subtitle_info),
        }
    ]
    story_info = chat_with_model(api_key=api_key, model_type="qwen", model="qwen-max", messages=messages)
    print(f"故事信息：\n{story_info}\n")

    for image_url_info in image_url_info_list:
        # 根据图片信息，重新生成生图提示词
        image_url = image_url_info["url"]
        image_info = image_url_info["info"]
        messages = [
            {
                "role": "system",
                "content": prompt.IMAGE_PROMPT_SYNC_SYSTEM_TEMPLATE,
            },
            {
                "role": "user",
                "content": prompt.IMAGE_PROMPT_SYNC_USER_TEMPLATE.substitute(image_info=image_info),
            }
        ]
        image_sync_prompt = chat_with_model(api_key=api_key, model_type="qwen", model="qwen-max", messages=messages)
        logger.info(f"🎨 生成的绘画提示词：\n{image_sync_prompt}")

        # 根据生图提示词生图
        new_image_path, new_image_url = sync_i2i_wan_v25(
            api_key=api_key,
            prompt=image_sync_prompt,
            images=[image_url],
            # images=image_url,
            save_dir=cfg.PICTURE_RESULTS_DIR
        )
        # 根据生图提示词生图
        # new_image_path, new_image_url = sync_t2i_wan_v25(
        #     api_key=api_key,
        #     prompt=image_sync_prompt,
        #     save_dir=cfg.PICTURE_RESULTS_DIR
        # )
        logger.info(f"🎉 新图片生成成功：\n{new_image_path}")

    return new_image_path, new_image_url


def image_sync_from_image_with_image2image(api_key, image_path, instruction, if_move_watermark=False):
    """
        通过图片编辑，重新生成图片
        :param api_key:
        :param image_path:
        :param instruction:
        :param if_move_watermark:
        :return:
        """

    # 生成图片url
    image_url = upload_file_to_oss(image_path, 300)

    if if_move_watermark:
        # 去水印和字幕
        _, res_url_list = synthesis_picture_with_wan(
            api_key=api_key,
            model_name="wanx2.1-imageedit",
            function="remove_watermark",
            prompt="去除图片中的水印和字幕",
            save_dir=cfg.PICTURE_RESULTS_DIR,
            base_image_url=image_url,
        )
        if image_url:
            image_url = res_url_list[0]
            logger.info(f"🎉 去水印和字幕成功：\n{image_url}")
        else:
            logger.error("❌ 去水印和字幕失败")
            return None, None
    else:
        pass

    image_edit_prompt = f'''
        请根据以下要求编辑输入的图片：
        保留主题: 确保最终图像仍然传达与原图相似的主题和情感。例如，如果原图展示的是一个宁静的自然景观，请保持这种宁静感。
        改变风格: 采用不同的艺术风格或色彩方案，例如，使用印象派风格的笔触，或将色调调整为更温暖或更冷的色调，以创造一种全新的视觉效果。
        添加元素: 在原图的基础上，可以添加一些新的元素或细节，比如在风景中加入一些动物，或在城市景观中增加一些人群活动，丰富画面内容。
        改变构图: 重新构图，改变主要焦点的位置，使观众的注意力集中在新的元素上，而不是原来的中心点。
        隐蔽原图特征: 在编辑过程中，确保原图的特征不易被识别，例如，通过模糊处理、变形或重组图像元素，使其看起来像全新的作品。
        保持故事连贯性: 尽管进行了显著的更改，但确保新图像仍然能够讲述一个连贯的故事，观众能理解其与原图的联系。
        请开始编辑，并确保最终作品具有独特性和创意，同时不失去原图的核心故事。
        {instruction}
    '''
    image_edit_prompt = '''
    转换成法国绘本风格
    '''
    image_edit_prompt = '''
    高级提示词：主题再创作 (Advanced Prompt: Thematic Reinterpretation)
    总指令：
    请严格遵循以下两步流程，对输入的图片进行一次深度的“主题再创作”。最终目标是生成一张在视觉上与原图毫无关联，但在情感和叙事上与原图高度一致的新作品。
    
    第一步：分析并锁定不变的核心 ——【叙事与氛围】
    
    任务： 首先，请深入分析原图，并用一句话精准定义其核心的 [叙事与氛围 (Narrative & Mood)]。这是你整个创作过程中唯一需要坚守的锚点。
    示例：
    如果原图是一个男人在拥挤地铁上发呆，其核心氛围可能是：“喧嚣都市背景下个体的深刻孤独与疏离感”。
    如果原图是暴风雨来临前的海面，其核心氛围可能是：“一种表面宁静之下，充满张力与压迫感的期待”。
    第二步：彻底重塑所有变化的要素 ——【视觉语言】
    
    在牢牢锁定核心的 [叙事与氛围] 之后，你必须完全抛弃并重塑原图的所有视觉元素。请在以下三个维度上进行最大程度的创新：
    
    物象与内容 (Subject & Content) -> 必须彻底替换
    
    指令： 创造全新的主体与环境来表达已锁定的氛围。不要使用原图中的任何物象。
    创意触发点： 如果原图是人物，尝试用静物、动物或纯粹的自然景观来表达相同的情感。如果原图是写实的，尝试用抽象的符号或概念。
    示例（对应“都市孤独感”）： 将“地铁上的男人”替换为“在万家灯火的城市夜景中，一扇没有开灯的窗户”，或者“在空旷停车场里，一辆孤零零的购物车”。
    构图与框架 (Composition & Framing) -> 必须重新设计
    
    指令： 采用与原图截然不同的构图、视角和取景。
    创意触发点： 如果原图是平视、对称的构图，请尝试使用极端的俯视/仰视，或对角线引导线。如果原图是全景，请尝试使用特写来聚焦于某个能体现氛围的细节。
    示例（对应“窗户”）： 放弃原图的正面构图，改为从一个极远、极高的角度俯瞰那片建筑，让黑暗的窗户在画面中只占很小一部分，以强调其渺小与孤立。
    视觉与技术 (Visual & Technical Execution) -> 必须风格迥异
    
    指令： 选择一个全新的艺术媒介、色彩方案和光影模型。
    创意触发点：
    媒介： 将照片风格变为水墨画、版画、赛博朋克3D渲染、超现实主义油画或刺绣/织物风格。
    色彩： 如果原图是彩色，尝试使用高对比度的黑白；如果原图是暖色调，请使用冰冷的蓝色或绿色为主色盘。
    光影： 将柔和的自然光变为戏剧性的、边缘锐利的伦勃朗光，或霓虹灯般的诡异光照。
    示例（对应“窗户”）： 采用高对比度黑白摄影风格，光线只照亮周围建筑的边缘，而那扇窗户则完全陷入黑暗，形成一个“负空间”的焦点。
    '''

    # 根据wan2.1 编辑生图
    # new_image_path, new_image_url = synthesis_picture_with_wan(
    #     api_key=api_key,
    #     model_name="wanx2.1-imageedit",
    #     function="description_edit",
    #     prompt=image_edit_prompt,
    #     save_dir=cfg.PICTURE_RESULTS_DIR,
    #     base_image_url=image_url,
    #     strength=0.9,
    # )
    # logger.info(f"🎉 新图片生成成功：\n{new_image_path}")

    # 根据wan2.5 编辑生图
    new_image_path, new_image_url = synthesis_picture_with_wan(
        api_key=api_key,
        model_name="wan2.5-i2i-preview",
        prompt=image_edit_prompt,
        negative_prompt="",
        save_dir=cfg.PICTURE_RESULTS_DIR,
        images=[image_url],
    )
    logger.info(f"🎉 新图片生成成功：\n{new_image_path}")

    return new_image_path, new_image_url


def test_sync_image(api_key):
    # 根据图片信息，重新生成生图提示词
    image_path = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0001.jpg"
    # image_url = upload_file_to_oss(image_path, 7200)
    image_url = "https://my-files-csy.oss-cn-hangzhou.aliyuncs.com/auto_uploads%2F1762844851_segment_001_frame_0001.jpg?OSSAccessKeyId=LTAI5t9pMQmrtoHAsxeQrXxV&Expires=1762852052&Signature=vfU2jfmGiJB6xri5hx8eUVapAZM%3D"
    image_info = '''
    ```json\n{\n  "scene": {\n    "environment": "室内",\n    "location": "厨房或屠宰场",\n    "time": "白天",\n    "weather": "人工照明"\n  },\n  "subjects": {\n    "people": [\n      {\n        "count": 6,\n        "appearance": "多名穿着白色厨师服、黑色围裙和帽子的厨师，部分可见面部表情专注。",\n        "pose": "多人围绕一头巨大的动物尸体进行切割作业，姿态各异，有的弯腰用刀，有的搬运肉块。",\n        "expression": "表情专注，部分因用力而显紧张。"\n      }\n    ],\n    "objects": [\n      {\n        "name": "大型动物尸体",\n        "description": "体型巨大，类似霸王龙的完整躯体，皮肤呈棕褐色，已被部分剥皮。",\n        "position": "位于画面中央，是所有厨师操作的核心对象。"\n      },\n      {\n        "name": "肉块",\n        "description": "从动物尸体上切割下来的大量红色生肉，堆放在地面上。",\n        "position": "分布在动物尸体周围及前景区域。"\n      },\n      {\n        "name": "刀具",\n        "description": "厨师们使用的长柄砍刀，用于分割巨大的肉块。",\n        "position": "由厨师手持，集中在动物尸体的关键部位。"\n      }\n    ]\n  },\n  "composition": {\n    "layout": "居中构图，以动物尸体为核心。",\n    "perspective": "平视视角，近距离拍摄，突出场景的混乱与规模。",\n    "depth": "景深较浅，焦点集中在厨师和动物尸体上，背景略显模糊。"\n  },\n  "visual_style": {\n    "color_tone": "暖色调，带有血红色调。",\n    "lighting": "人工顶灯照明，光线明亮但略显冷硬。",\n    "atmosphere": "紧张、混乱且略带幽默感。",\n    "art_style": "写实风格，模拟真实场景。"\n  },\n  "details": {\n    "foreground": "地面上散落着大量血迹和肉块，增加了场景的视觉冲击力。",\n    "background": "可见厨房设备、金属操作台和悬挂的灯具，进一步强化了工业化的环境氛围。",\n    "notable_features": "厨师们分工协作，场面宏大，模仿了经典烹饪节目《地狱厨房》的风格，但加入了恐龙这一超现实元素，营造出荒诞搞笑的效果。"\n  }\n}\n```'
    '''
    story_info = '''
    ```json
{
  "theme": {
    "main_idea": "搞笑",
    "emotion": "欢乐"
  },
  "background": {
    "time": "现代",
    "location": "厨房（模仿地狱厨房的综艺节目现场）"
  },
  "characters": [
    {
      "role": "厨师",
      "traits": [
        "专注",
        "紧张",
        "分工协作"
      ]
    },
    {
      "role": "主持人",
      "traits": [
        "夸张",
        "幽默"
      ]
    }
  ],
  "plot": {
    "introduction": "六位来自全球的新厨师面临烹饪一只已经灭绝了6500万年的霸王龙的挑战。",
    "conflict": "厨师们在极端压力下处理不寻常且荒谬的任务，即烹饪一只大型霸王龙。",
    "climax": "主持人用夸张的语言和比喻批评厨师们的表现，制造出紧张而幽默的气氛。",
    "ending": "视频以主持人的命令“出去！出去！”结束，暗示至少一位厨师可能被淘汰，但整体氛围轻松戏谑。"
  },
  "purpose": {
    "message": "通过模仿著名烹饪节目《地狱厨房》的形式，并加入超现实元素如烹饪恐龙，为观众提供新颖独特的娱乐体验。"
  }
}
```
    '''

    # messages = [
    #     {
    #         "role": "system",
    #         "content": prompt.IMAGE_PROMPT_SYNC_SYSTEM_TEMPLATE,
    #     },
    #     {
    #         "role": "user",
    #         "content": prompt.IMAGE_PROMPT_SYNC_USER_TEMPLATE.substitute(image_info=image_info+story_info),
    #     }
    # ]
    # image_sync_prompt = chat_with_model(api_key=api_key, model_type="qwen", model="qwen-max", messages=messages, extra_body={"enable_thinking": True})
    # logger.info(f"🎨 生成的绘画提示词：\n{image_sync_prompt}")

    image_sync_prompt = "six chefs in white uniforms and black aprons, focused expressions, working on a large dinosaur carcass, various poses, cutting and moving meat, large dinosaur carcass, partially skinned, brownish skin, located in the center, red raw meat chunks, scattered on the ground, long-handled cleavers, held by chefs, kitchen environment, industrial setting, bright artificial lighting, warm color tone with blood red, chaotic and humorous atmosphere, realistic style, central composition, close-up perspective, shallow depth of field, foreground with blood and meat, background with kitchen equipment and metal workstations, 720P resolution, detailed, high quality"

    # 根据生图提示词生图
    new_image_path, new_image_url = sync_i2i_wan_v25(
        api_key=api_key,
        prompt=image_sync_prompt,
        images=[image_url],
        # images=image_url,
        save_dir=cfg.PICTURE_RESULTS_DIR
    )
    # 根据生图提示词生图
    # new_image_path, new_image_url = sync_t2i_wan_v25(
    #     api_key=api_key,
    #     prompt=image_sync_prompt,
    #     save_dir=cfg.PICTURE_RESULTS_DIR
    # )
    logger.info(f"🎉 新图片生成成功：\n{new_image_path}")


def sync_new_story(
    api_key: str, 
    images_info: str, 
    subtitle: str, 
    instruction: str
) -> dict:
    """
    基于原视频信息生成新故事
    
    Args:
        api_key: API密钥
        images_info: 图片结构化信息
        subtitle: 字幕文本
        instruction: 用户指令（如：改编为科幻风格）
        
    Returns:
        新故事的结构化JSON dict
    """
    
    # ========================================
    # 步骤1：提取原故事摘要
    # ========================================
    logger.info("📖 步骤1：提取原故事摘要...")
    
    messages = [
        {
            "role": "system",
            "content": prompt.STORY_EXTRACT_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_EXTRACT_USER_TEMPLATE.substitute(
                instruction=instruction,
                images_info=images_info,
                subtitle_info=subtitle
            ),
        }
    ]
    ori_story = chat_with_model(
        api_key=api_key, 
        model_type="qwen", 
        model="qwen-max", 
        messages=messages
    )
    logger.info(f"✅ 原故事摘要：\n{ori_story}\n")
    
    
    # ========================================
    # 步骤2：生成3个新故事创意
    # ========================================
    logger.info("💡 步骤2：生成3个新故事创意...")
    
    messages = [
        {
            "role": "system",
            "content": prompt.STORY_IDEA_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_IDEA_USER_TEMPLATE.substitute(
                ori_story=ori_story,
                instruction=instruction
            ),
        }
    ]
    
    new_story_ideas = []
    for i in range(3):
        logger.info(f"  生成创意 {i+1}/3...")
        idea = chat_with_model(
            api_key=api_key, 
            model_type="deepseek",
            model="deepseek-v3.2-exp",
            extra_body={"enable_thinking": True},
            messages=messages
        )
        new_story_ideas.append(idea)
        logger.info(f"  ✅ 创意{i+1}：{idea[:100]}...\n")
    
    
    # ========================================
    # 步骤3：选择最佳创意
    # ========================================
    logger.info("🎯 步骤3：选择最佳创意...")
    
    messages = [
        {
            "role": "system",
            "content": prompt.STORY_IDEA_SELECT_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_IDEA_SELECT_USER_TEMPLATE.substitute(
                idea_1=new_story_ideas[0],
                idea_2=new_story_ideas[1],
                idea_3=new_story_ideas[2],
                instruction=instruction
            ),
        }
    ]
    
    selection_result = chat_with_model(
        api_key=api_key, 
        model_type="qwen", 
        model="qwen-plus",
        extra_body={"enable_thinking": True},
        messages=messages
    )
    logger.info(f"✅ 选择结果：\n{selection_result}\n")
    
    # 解析选择结果（简单处理：查找创意编号）
    selected_idx = 0  # 默认选第一个
    if "创意2" in selection_result or "idea 2" in selection_result.lower() or "编号2" in selection_result:
        selected_idx = 1
    elif "创意3" in selection_result or "idea 3" in selection_result.lower() or "编号3" in selection_result:
        selected_idx = 2
    
    final_idea = new_story_ideas[selected_idx]
    logger.info(f"🎉 最终选定创意{selected_idx+1}")
    
    
    # ========================================
    # 步骤4：展开完整新故事
    # ========================================
    logger.info("📝 步骤4：展开完整新故事...")
    
    messages = [
        {
            "role": "system",
            "content": prompt.STORY_EXPAND_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_EXPAND_USER_TEMPLATE.substitute(
                final_idea=final_idea,
                reason=selection_result,
                instruction=instruction
            ),
        }
    ]
    
    new_story = chat_with_model(
        api_key=api_key, 
        model_type="qwen", 
        model="qwen-max", 
        messages=messages
    )
    logger.info(f"✅ 新故事生成完成：\n{new_story}\n")
    
    return {
        "ori_story": ori_story,
        "ideas": new_story_ideas,
        "selected_idea": final_idea,
        "selection_reason": selection_result,
        "new_story": new_story
    }


def sync_new_story_images(api_key: str, ori_images: list, new_story: str, instruction: str, negative_prompt: str = None, size: str = "1280*720"):
    # ========================================
    # 生成新的图提示词
    # ========================================
    new_image_path_list = []
    new_image_url_list = []
    logger.info("生成图提示词，开始...")
    for index, ori_image in enumerate(ori_images, start=1):

        # 打印当前循环进度
        logger.info(f"🔄 开始生成第 {index}/{len(ori_images)} 个生图提示词...")
        # 根据图片信息，重新生成生图提示词
        image_url = ori_image["url"]
        image_info = ori_image["info"]
        messages = [
            {
                "role": "system",
                "content": prompt.IMAGE_PROMPT_SYNC_SYSTEM_TEMPLATE,
            },
            {
                "role": "user",
                "content": prompt.IMAGE_PROMPT_SYNC_USER_TEMPLATE.substitute(image_info=image_info, new_story=new_story, instruction=instruction),
            }
        ]
        image_sync_prompt = chat_with_model(api_key=api_key, model_type="qwen", model="qwen-max", messages=messages)
        logger.info(f"🎨 第 {index} 个绘画提示词生成完成：\n{image_sync_prompt}")

        # 根据生图提示词生图
        logger.info(f"🔄 开始生成第 {index}/{len(ori_images)} 个新图...")
        new_image_path, new_image_url = sync_t2i_wan_v25(
            api_key=api_key,
            prompt=image_sync_prompt,
            negative_prompt=negative_prompt,
            size=size,
            save_dir=cfg.PICTURE_RESULTS_DIR
        )
        new_image_path_list.append(new_image_path)
        new_image_url_list.append(new_image_url)
        logger.info(f"✅ 第 {index} 个新图生成完成：新图已保存至：{new_image_path}")

    return new_image_path_list, new_image_url_list


if __name__ == "__main__":
    import os
    import time  # 添加时间模块
    from dotenv import load_dotenv
    from config.logging_config import setup_logging

    setup_logging()

    logger.info("📋 初始化配置参数")
    # hack csy 20251107:这个加载环境变量的方式，在不同的路径都会改变，回头有时间优化一下
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")

    # 检查API密钥是否成功加载
    if not api_key:
        raise ValueError("未找到DashScope API密钥，请检查环境变量DASHSCOPE_API_KEY是否正确配置")

    start_time = time.time()

    # # 待理解文件路径
    # test_image_path_list = [
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0001.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0003.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0006.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0010.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0011.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0016.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0020.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0021.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0022.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0023.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0024.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0025.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0026.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0028.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0029.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0030.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0031.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0034.jpg",
    #     "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0035.jpg",
    # ]
    test_image_path_list = [
        "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0001.jpg",
        "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0003.jpg",
        "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001/segment_001_frame_0006.jpg",
    ]
    images_info = '''
        ['```json\n{\n  "scene": {\n    "environment": "室内",\n    "location": "厨房或屠宰场",\n    "time": "白天",\n    "weather": "人工照明"\n  },\n  "subjects": {\n    "people": [\n      {\n        "count": 6,\n        "appearance": "多名穿着白色厨师服、黑色围裙和帽子的厨师，部分可见面部表情专注。",\n        "pose": "多人围绕一头巨大的动物尸体进行切割作业，姿态各异，有的弯腰用刀，有的搬运肉块。",\n        "expression": "表情专注，部分因用力而显紧张。"\n      }\n    ],\n    "objects": [\n      {\n        "name": "大型动物尸体",\n        "description": "体型巨大，类似霸王龙的完整躯体，皮肤呈棕褐色，已被部分剥皮。",\n        "position": "位于画面中央，是所有厨师操作的核心对象。"\n      },\n      {\n        "name": "肉块",\n        "description": "从动物尸体上切割下来的大量红色生肉，堆放在地面上。",\n        "position": "分布在动物尸体周围及前景区域。"\n      },\n      {\n        "name": "刀具",\n        "description": "厨师们使用的长柄砍刀，用于分割巨大的肉块。",\n        "position": "由厨师手持，集中在动物尸体的关键部位。"\n      }\n    ]\n  },\n  "composition": {\n    "layout": "居中构图，以动物尸体为核心。",\n    "perspective": "平视视角，近距离拍摄，突出场景的混乱与规模。",\n    "depth": "景深较浅，焦点集中在厨师和动物尸体上，背景略显模糊。"\n  },\n  "visual_style": {\n    "color_tone": "暖色调，带有血红色调。",\n    "lighting": "人工顶灯照明，光线明亮但略显冷硬。",\n    "atmosphere": "紧张、混乱且略带幽默感。",\n    "art_style": "写实风格，模拟真实场景。"\n  },\n  "details": {\n    "foreground": "地面上散落着大量血迹和肉块，增加了场景的视觉冲击力。",\n    "background": "可见厨房设备、金属操作台和悬挂的灯具，进一步强化了工业化的环境氛围。",\n    "notable_features": "厨师们分工协作，场面宏大，模仿了经典烹饪节目《地狱厨房》的风格，但加入了恐龙这一超现实元素，营造出荒诞搞笑的效果。"\n  }\n}\n```', '```json\n{\n  "scene": {\n    "environment": "室内",\n    "location": "厨房或肉类加工区",\n    "time": "白天",\n    "weather": "人工照明，光线充足"\n  },\n  "subjects": {\n    "people": [\n      {\n        "count": 5,\n        "appearance": "均穿着白色厨师服和高顶厨师帽，部分可见黑色裤子",\n        "pose": "正在处理大型肉块，使用刀具切割",\n        "expression": "因面部被遮挡，无法判断表情"\n      }\n    ],\n    "objects": [\n      {\n        "name": "大型肉块",\n        "description": "巨大的动物骨骼和肌肉组织，疑似模拟霸王龙的肉块",\n        "position": "位于画面左侧，占据显著位置"\n      },\n      {\n        "name": "工作台",\n        "description": "木质或石质的工作台面，表面有血迹和碎肉",\n        "position": "位于肉块下方，支撑着大型肉块"\n      },\n      {\n        "name": "刀具",\n        "description": "厨师手中握持的大型砍刀，用于切割肉块",\n        "position": "位于厨师手中，正接触肉块"\n      }\n    ]\n  },\n  "composition": {\n    "layout": "采用三分法构图，主体人物和肉块位于画面左侧，背景人物和设备延伸至右侧",\n    "perspective": "平视视角，略微仰视前方的厨师和肉块",\n    "depth": "景深效果明显，前景清晰，背景略显模糊"\n  },\n  "visual_style": {\n    "color_tone": "暖色调，带有红色和棕色的肉类色彩",\n    "lighting": "人工照明，灯光集中在工作区域，形成明暗对比",\n    "atmosphere": "紧张、忙碌，充满压力感",\n    "art_style": "写实风格，细节丰富，具有电影质感"\n  },\n  "details": {\n    "foreground": "大型肉块和厨师的特写，突出切割动作和肉块的细节",\n    "background": "其他厨师在后方工作，可见金属操作台和厨房设备",\n    "notable_features": "画面中央的厨师正专注地切割巨大的肉块，营造出一种高强度的烹饪氛围"\n  }\n}\n```', '```json\n{\n  "scene": {\n    "environment": "室内",\n    "location": "厨房",\n    "time": "白天",\n    "weather": "人工照明"\n  },\n  "subjects": {\n    "people": [\n      {\n        "count": 2,\n        "appearance": "一人戴着霸王龙头套，身穿黑色长袖上衣和黑色手套；另一人身穿白色厨师服，表情惊讶。",\n        "pose": "戴头套者双手端着一个装有大块牛排的白色盘子，厨师站在其右侧。",\n        "expression": "厨师表情夸张，眼睛睁大，嘴巴微张，显得非常震惊。"\n      }\n    ],\n    "objects": [\n      {\n        "name": "牛排",\n        "description": "一大块煎得半熟的牛排，表面油亮，放在一个白色的圆形盘子上。",\n        "position": "位于画面中央，由戴头套的人双手托着。"\n      }\n    ]\n  },\n  "composition": {\n    "layout": "居中构图，人物和牛排占据画面主要位置。",\n    "perspective": "平视视角，直接面对观众。",\n    "depth": "前景为人物和牛排，背景为厨房设备，层次分明。"\n  },\n  "visual_style": {\n    "color_tone": "暖色调，带有火焰的橙红色光效。",\n    "lighting": "人工灯光，突出牛排和人物面部表情。",\n    "atmosphere": "紧张且带有喜剧效果。",\n    "art_style": "电影感，细节丰富，色彩鲜明。"\n  },\n  "details": {\n    "foreground": "戴头套者手中的牛排盘子，细节清晰可见。",\n    "background": "厨房环境，可见炉灶、抽油烟机等设备，部分区域有火焰。",\n    "notable_features": "霸王龙头套与厨师服形成强烈对比，增加了戏剧性和幽默感。"\n  }\n}\n```']
        '''
    subtitle = "For years, one kitchen has defined the absolute peak of culinary pressure. You put so much oil in this, the U.S. is trying to invade the plate. It is a battleground where dreams are forged in fire or crushed into ashes. This scallop is so raw, I can still hear it telling SpongeBob to fuck off. Tonight, six new chefs from across the globe step into the arena, but they will not be cooking lamb or beef or scallops. Tonight, they face a challenge that has been extinct for 65 million years and only one black jacket. Get out! Get out!"
    images_dict_list = [
    {
        "info": "{\"scene\":{\"environment\":\"室内\",\"location\":\"厨房或屠宰场\",\"time\":\"白天\",\"weather\":\"人工照明\"},\"subjects\":{\"people\":[{\"count\":6,\"appearance\":\"多名穿着白色厨师服、黑色围裙和帽子的厨师，部分可见面部表情专注。\",\"pose\":\"多人围绕一头巨大的动物尸体进行切割作业，姿态各异，有的弯腰用刀，有的搬运肉块。\",\"expression\":\"表情专注，部分因用力而显紧张。\"}],\"objects\":[{\"name\":\"大型动物尸体\",\"description\":\"体型巨大，类似霸王龙的完整躯体，皮肤呈棕褐色，已被部分剥皮。\",\"position\":\"位于画面中央，是所有厨师操作的核心对象。\"},{\"name\":\"肉块\",\"description\":\"从动物尸体上切割下来的大量红色生肉，堆放在地面上。\",\"position\":\"分布在动物尸体周围及前景区域。\"},{\"name\":\"刀具\",\"description\":\"厨师们使用的长柄砍刀，用于分割巨大的肉块。\",\"position\":\"由厨师手持，集中在动物尸体的关键部位。\"}]},\"composition\":{\"layout\":\"居中构图，以动物尸体为核心。\",\"perspective\":\"平视视角，近距离拍摄，突出场景的混乱与规模。\",\"depth\":\"景深较浅，焦点集中在厨师和动物尸体上，背景略显模糊。\"},\"visual_style\":{\"color_tone\":\"暖色调，带有血红色调。\",\"lighting\":\"人工顶灯照明，光线明亮但略显冷硬。\",\"atmosphere\":\"紧张、混乱且略带幽默感。\",\"art_style\":\"写实风格，模拟真实场景。\"},\"details\":{\"foreground\":\"地面上散落着大量血迹和肉块，增加了场景的视觉冲击力。\",\"background\":\"可见厨房设备、金属操作台和悬挂的灯具，进一步强化了工业化的环境氛围。\",\"notable_features\":\"厨师们分工协作，场面宏大，模仿了经典烹饪节目《地狱厨房》的风格，但加入了恐龙这一超现实元素，营造出荒诞搞笑的效果。\"}}",
        "url": ""
    },
    {
        "info": "{\"scene\":{\"environment\":\"室内\",\"location\":\"厨房或肉类加工区\",\"time\":\"白天\",\"weather\":\"人工照明，光线充足\"},\"subjects\":{\"people\":[{\"count\":5,\"appearance\":\"均穿着白色厨师服和高顶厨师帽，部分可见黑色裤子\",\"pose\":\"正在处理大型肉块，使用刀具切割\",\"expression\":\"因面部被遮挡，无法判断表情\"}],\"objects\":[{\"name\":\"大型肉块\",\"description\":\"巨大的动物骨骼和肌肉组织，疑似模拟霸王龙的肉块\",\"position\":\"位于画面左侧，占据显著位置\"},{\"name\":\"工作台\",\"description\":\"木质或石质的工作台面，表面有血迹和碎肉\",\"position\":\"位于肉块下方，支撑着大型肉块\"},{\"name\":\"刀具\",\"description\":\"厨师手中握持的大型砍刀，用于切割肉块\",\"position\":\"位于厨师手中，正接触肉块\"}]},\"composition\":{\"layout\":\"采用三分法构图，主体人物和肉块位于画面左侧，背景人物和设备延伸至右侧\",\"perspective\":\"平视视角，略微仰视前方的厨师和肉块\",\"depth\":\"景深效果明显，前景清晰，背景略显模糊\"},\"visual_style\":{\"color_tone\":\"暖色调，带有红色和棕色的肉类色彩\",\"lighting\":\"人工照明，灯光集中在工作区域，形成明暗对比\",\"atmosphere\":\"紧张、忙碌，充满压力感\",\"art_style\":\"写实风格，细节丰富，具有电影质感\"},\"details\":{\"foreground\":\"大型肉块和厨师的特写，突出切割动作和肉块的细节\",\"background\":\"其他厨师在后方工作，可见金属操作台和厨房设备\",\"notable_features\":\"画面中央的厨师正专注地切割巨大的肉块，营造出一种高强度的烹饪氛围\"}}",
        "url": ""
    },
    {
        "info": "{\"scene\":{\"environment\":\"室内\",\"location\":\"厨房\",\"time\":\"白天\",\"weather\":\"人工照明\"},\"subjects\":{\"people\":[{\"count\":2,\"appearance\":\"一人戴着霸王龙头套，身穿黑色长袖上衣和黑色手套；另一人身穿白色厨师服，表情惊讶。\",\"pose\":\"戴头套者双手端着一个装有大块牛排的白色盘子，厨师站在其右侧。\",\"expression\":\"厨师表情夸张，眼睛睁大，嘴巴微张，显得非常震惊。\"}],\"objects\":[{\"name\":\"牛排\",\"description\":\"一大块煎得半熟的牛排，表面油亮，放在一个白色的圆形盘子上。\",\"position\":\"位于画面中央，由戴头套的人双手托着。\"}]},\"composition\":{\"layout\":\"居中构图，人物和牛排占据画面主要位置。\",\"perspective\":\"平视视角，直接面对观众。\",\"depth\":\"前景为人物和牛排，背景为厨房设备，层次分明。\"},\"visual_style\":{\"color_tone\":\"暖色调，带有火焰的橙红色光效。\",\"lighting\":\"人工灯光，突出牛排和人物面部表情。\",\"atmosphere\":\"紧张且带有喜剧效果。\",\"art_style\":\"电影感，细节丰富，色彩鲜明。\"},\"details\":{\"foreground\":\"戴头套者手中的牛排盘子，细节清晰可见。\",\"background\":\"厨房环境，可见炉灶、抽油烟机等设备，部分区域有火焰。\",\"notable_features\":\"霸王龙头套与厨师服形成强烈对比，增加了戏剧性和幽默感。\"}}",
        "url": ""
    }
]
    new_story = '''
    ```json
{
  "title": "星际大厨争夺战",
  "theme": {
    "main_idea": "团队协作与个人表现之间的平衡",
    "emotion": "紧张与幽默"
  },
  "setting": {
    "time": "未来某日",
    "location": "高科技厨房",
    "visual_description": "充满未来感的厨房，设备先进，灯光闪烁"
  },
  "characters": [
    {
      "role": "机器人厨师A",
      "traits": ["高效", "冷静"],
      "appearance": "银色金属外壳，带有机械臂",
      "motivation": "赢得“星际大厨”徽章"
    },
    {
      "role": "机器人厨师B",
      "traits": ["笨拙", "乐观"],
      "appearance": "蓝色金属外壳，带有机械臂",
      "motivation": "证明自己"
    },
    {
      "role": "闪光外星人评委",
      "traits": ["夸张", "挑剔"],
      "appearance": "穿着闪亮服装，头戴天线帽",
      "motivation": "选出最佳厨师"
    }
  ],
  "plot": {
    "hook": "一群机器人厨师在高科技厨房中忙碌，突然一个巨大的发光蘑菇出现在中央。",
    "setup": "评委宣布比赛规则：谁能在最短时间内完美处理这个外星蘑菇，就能获得‘星际大厨’徽章。",
    "conflict": "机器人厨师们开始分工合作，但过程中出现各种搞笑失误，如切割不均、调料洒落等。",
    "climax": "关键时刻，机器人厨师A冷静指挥，成功完成任务，而机器人厨师B则因一系列失误被回收。",
    "resolution": "评委宣布机器人厨师A获胜，并颁发‘星际大厨’徽章，其他机器人被回收。"
  },
  "visual_style": {
    "art_style": "写实",
    "color_palette": "冷色调",
    "lighting": "明亮",
    "key_scenes": ["巨型蘑菇登场", "机器人厨师分工协作", "机器人厨师A指挥", "颁奖时刻"]
  },
  "narrative_style": {
    "tone": "轻松",
    "pacing": "快速",
    "music_style": "欢快"
  }
}
```
    '''

    # new_image_path, new_image_url = image_sync_from_image_with_text2image(api_key, test_image_path, "这是一个在模仿地狱厨房的综艺节目，烹饪大型霸王龙的搞笑视频")
    # new_image_path, new_image_url = image_sync_from_image_with_image2image(api_key, test_image_path, "", if_move_watermark=False)
    # image_sync_from_images8subtitle_with_text2image(api_key, test_image_path_list, subtitle, "这是一个在模仿地狱厨房的综艺节目，烹饪大型霸王龙的搞笑视频")

    # test_sync_image(api_key)

    # res = sync_new_story(api_key, images_info, subtitle, "")
    # print(f"res:\n{res}\n")

    new_image_path, new_image_url = sync_new_story_images(api_key, images_dict_list, new_story, "", "", "1280*720")

    # 记录结束时间并计算运行时间
    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")

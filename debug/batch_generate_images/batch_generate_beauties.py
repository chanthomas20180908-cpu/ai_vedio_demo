"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 批量生成历史美女的写实摄影风格图片
Output: 生成的图片文件和URL
Pos: 测试文件：batch_generate_beauties.py
"""

import os
from dotenv import load_dotenv
from config.logging_config import setup_logging
from component.muti.synthesis_image import sync_t2i_wan_v25
import webbrowser
import time


# 定义15个历史美女的提示词
BEAUTY_CHARACTER_PROMPTS = [
    # 中国古代美女 (6个)
    {
        "name": "杨贵妃_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,杨贵妃唐朝形象,四大美女之一,
丰满圆润的鹅蛋脸,精致的五官,澄亮的黑色眼睛,
华丽的唐朝高髻,装饰着珍珠翠玉发饰,
穿着雍容华贵的唐朝宫廷礼服,色彩鲜艳,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和宫廷光照,背景金色华丽虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 360
    },
    {
        "name": "西施_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,西施春秋时期形象,四大美女之一,
清秀的瓜子脸,柳叶眉,杏眼,樱桃小口,
简洁的发髻,只用简单的木簪固定,
穿着素雅的白色汉服,流仙飘逸,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
自然柔和光照,背景水边樱花虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 370
    },
    {
        "name": "貂蝉_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,貂蝉三国时期形象,四大美女之一,
精致的鹅蛋脸,月眉星眼,高雅端庄,
精致的发髻,装饰着珠花发饰,
穿着华丽的汉服宫装,色彩丰富,
上半身肖像,3/4侧面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
古典肖像光照,背景深色虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 380
    },
    {
        "name": "王昭君_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,王昭君汉朝形象,四大美女之一,
端庄的鹅蛋脸,柳叶眉,深邃的眼神,
简洁的发髻,只用简单的发饰,
穿着素雅的汉服,带有一丝忧郁,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和自然光照,背景远山冷调虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 390
    },
    {
        "name": "武则天_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,武则天唐朝女皇形象,
端庄威严的面容,凤眼,立体的五官,
华丽高贵的高髻,金色凤凰发冠,
穿着金色龙袍的帝王服饰,雍容华贵,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
庄重宫廷光照,背景金色龙纹虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 400
    },
    {
        "name": "赵飞燕_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,赵飞燕汉朝皇后形象,
轻盈纤细的鹅蛋脸,灵动的眼睛,
优雅的高髻,装饰着珍珠发饰,
穿着轻盈的汉朝宫装,色彩淡雅,
上半身肖像,3/4侧面朝向镜头,姿态优雅,
细腻的皮肤纹理,真实的光影效果,
柔和宫廷光照,背景淡色虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 410
    },
    
    # 欧洲传奇美女 (5个)
    {
        "name": "克利奥帕特拉_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,克利奥帕特拉埃及艳后形象,
异域风情的精致面容,浓黑的眼线,高雅的鼻梁,
标志性的黑色长直发,金色眼镜蛇头饰,
穿着华丽的古埃及白色亚麻长袍,金色项圈,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
神秘古埃及光照,背景金色金字塔虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 420
    },
    {
        "name": "茜茜公主_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,茜茜公主(伊丽莎白皇后)奥匈帝国形象,
精致的瓜子脸,柴叶眉,深邃的眼睛,
精致的高发髻,装饰着钻石星星发饰,
穿着19世纪华丽的宫廷礼服,白色为主,
上半身肖像,3/4侧面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
优雅宫廷光照,背景华丽宫殿虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 430
    },
    {
        "name": "戴安娜王妃_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,戴安娜王妃现代形象,
精致的瓜子脸,温柔的眼神,甜美的微笑,
优雅的短发造型,金色的头发,
穿着优雅的现代礼服或晚礼服,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和自然光照,背景淡雅虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 440
    },
    {
        "name": "海伦_特洛伊_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,特洛伊的海伦古希腊形象,
精致的鹅蛋脸,清秀的五官,深邃的蓝色眼睛,
金色的波浪卷发,用白色缎布轻轻缠绕,
穿着古希腊白色长袍,简洁优雅,
上半身肖像,3/4侧面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和自然光照,背景地中海蓝天虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 450
    },
    {
        "name": "约瑟芬皇后_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,约瑟芬皇后(拿破仑妻子)法国帝国形象,
优雅的鹅蛋脸,温柔的眼神,甜美的微笑,
优雅的高发髻,金色帝国皇冠,
穿着帝国风格的白色高腰长裙,珍珠项链,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
优雅宫廷光照,背景华丽宫殿虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 460
    },
    
    # 神话传说美女 (4个)
    {
        "name": "嫦娥_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,嫦娥仙女形象,
美丽的鹅蛋脸,清冷而温柔的眼神,
飘逸的黑色长发,只用简单的云髻固定,
穿着白色的飘逸仙衫,轻盈灵动,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和月光照明,背景月亮星空虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 470
    },
    {
        "name": "织女_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,织女仙女形象,
温柔的瓜子脸,柔和的眼神,甜美的微笑,
黑色的长发编成精致的发髻,云形发饰,
穿着粉色或淡蓝色的仙衫,柔美飘逸,
上半身肖像,3/4侧面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和仙境光照,背景七夕星空虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 480
    },
    {
        "name": "七仙女_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,七仙女(代表形象)仙女形象,
美丽的鹅蛋脸,明亮的眼睛,活泼的笑容,
飘逸的黑色长发,精致的仙女发髻,
穿着五彩缤纷的仙衫,色彩鲜艳,
上半身肖像,正面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
明亮仙境光照,背景五彩云彩虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 490
    },
    {
        "name": "白素贞_写实",
        "style": "写实摄影",
        "prompt": """
高分辨率写实肖像摄影,白素贞(白娘子)传说形象,
清秀的瓜子脸,温柔的眼神,慈爱的微笑,
飘逸的黑色长发,简单的发髻,
穿着纯白色的仙衫,灵动飘逸,
上半身肖像,3/4侧面朝向镜头,
细腻的皮肤纹理,真实的光影效果,
柔和自然光照,背景西湖山水虚化,
专业人像摄影质量,电影级画质,超高清细节
""",
        "negative_prompt": "3D渲染,卡通,动漫,插画,低质量,模糊,变形,多余的肢体,水印,文字,logo",
        "seed": 500
    }
]


def batch_generate_beauties():
    """批量生成历史美女图片"""
    
    # 初始化日志
    setup_logging()
    
    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # 检查API密钥
    if not api_key:
        raise ValueError("未找到DashScope API密钥，请检查环境变量配置")
    
    print("=" * 70)
    print("开始批量生成历史美女写实摄影图片")
    print(f"共需生成 {len(BEAUTY_CHARACTER_PROMPTS)} 个角色")
    print("包含: 中国古代美女(6) + 欧洲传奇美女(5) + 神话传说美女(4)")
    print("=" * 70)
    print()
    
    results = []
    
    for idx, character in enumerate(BEAUTY_CHARACTER_PROMPTS, 1):
        print(f"[{idx}/{len(BEAUTY_CHARACTER_PROMPTS)}] 正在生成: {character['name']}")
        print("-" * 70)
        
        try:
            # 使用角色预定义的seed值和negative_prompt
            seed = character['seed']
            negative_prompt = character['negative_prompt']
            style = character['style']
            
            print(f"   风格: {style}")
            print(f"   Seed: {seed}")
            
            image_path, image_url = sync_t2i_wan_v25(
                api_key=api_key,
                prompt=character['prompt'],
                negative_prompt=negative_prompt,
                size="1024*1024",
                seed=seed,
                n=1
            )
            
            if image_url and image_path:
                print(f"✅ {character['name']} 生成成功!")
                print(f"   图片URL: {image_url}")
                print(f"   本地路径: {image_path}")
                
                results.append({
                    "name": character['name'],
                    "status": "成功",
                    "path": image_path,
                    "url": image_url
                })
                
            else:
                print(f"❌ {character['name']} 生成失败")
                results.append({
                    "name": character['name'],
                    "status": "失败",
                    "path": None,
                    "url": None
                })
        
        except Exception as e:
            print(f"❌ {character['name']} 生成出错: {str(e)}")
            results.append({
                "name": character['name'],
                "status": "出错",
                "path": None,
                "url": None,
                "error": str(e)
            })
        
        print()
        
        # 避免API调用过快，添加短暂延迟
        if idx < len(BEAUTY_CHARACTER_PROMPTS):
            time.sleep(2)
    
    # 输出汇总结果
    print("=" * 70)
    print("生成完成！汇总结果:")
    print("=" * 70)
    
    success_count = 0
    for result in results:
        status_icon = "✅" if result['status'] == "成功" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if result['status'] == "成功":
            success_count += 1
            print(f"   路径: {result['path']}")
    
    print()
    print(f"成功: {success_count}/{len(BEAUTY_CHARACTER_PROMPTS)}")
    
    # 自动打开图片
    if success_count > 0:
        print()
        print("正在自动打开成功生成的图片...")
        time.sleep(1)
        
        for result in results:
            if result['status'] == "成功" and result['path']:
                clean_path = result['path'].split('?')[0]
                if os.path.exists(clean_path):
                    webbrowser.open(f"file://{clean_path}")
                    time.sleep(0.5)


if __name__ == "__main__":
    batch_generate_beauties()
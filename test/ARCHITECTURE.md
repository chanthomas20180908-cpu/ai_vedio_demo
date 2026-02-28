# Test 目录架构说明

**⚠️ 一旦我所属的文件夹有所变化，请更新我。**

## 架构概览
测试代码目录，包含各类功能测试、视频处理测试和实验性代码。

## 文件清单

### 视频处理相关测试
- **extract_frames.py** - 视频帧提取测试
- **extract_video_srt.py** - 视频字幕提取测试
- **split_video_by_srt.py** - 根据字幕分割视频
- **process_video_demo.py** - 视频处理演示

### 多模态测试
- **test_i2v_doubao.py** - 豆包图生视频测试
- **test_i2v_minimax.py** - MiniMax 图生视频测试
- **test_image_sync_from_image.py** - 图像同步测试
- **test_vedio_talk.py** - 视频对话测试

### 功能测试
- **test_001.py** / **test_002.py** - 基础功能测试
- **test_content_inspection.py** - 内容检查测试
- **test_directory_context.py** - 目录上下文测试
- **test_dynamic_scraper.py** - 动态爬虫测试
- **test_interactive_agent.py** - 交互式 Agent 测试
- **test_new_mdl.py** - 新模型测试
- **test_web_tools_multimode.py** - 多模式 Web 工具测试
- **test_taobao_advanced.py** - 淘宝高级功能测试

### 数据处理测试
- **parse_json_bak.py** - JSON 解析备份
- **separate_json.py** - JSON 分离
- **test_split_json.py** - JSON 分割测试
- **simple_transcribe.py** - 简单转录
- **test_diarization.py** - 说话人分离测试

### 子目录

#### parse_json/ - JSON 解析
- **try_parse_json.py** - JSON 解析尝试
- **debug_parse_json.py** - JSON 解析调试
- **__init__.py** - 包初始化文件

#### comidian_ai/ - 喜剧 AI
- **standup_game_core.py** - 单口喜剧游戏核心
- **test_standup_game.py** - 单口喜剧游戏测试
- **debug_punchline.py** - 笑点调试

#### test_meme_make/ - 表情包制作测试
- **test_process_short_vedio.py** - 短视频处理测试
- **__init__.py** - 包初始化文件

#### comedian/ - 喜剧相关
- 喜剧内容存储目录

#### frames_001/ - 帧数据
- 视频帧数据存储目录

### __init__.py
- 测试包初始化文件

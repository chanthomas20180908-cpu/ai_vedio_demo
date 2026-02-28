# Component 目录架构说明

**⚠️ 一旦我所属的文件夹有所变化，请更新我。**

## 架构概览
组件层，提供聊天对话、多模态内容合成等高层应用组件，是系统功能的主要实现层。

## 文件清单

### chat/ 子目录 - 聊天对话组件
- **chat.py** - 基础聊天功能实现
- **unified_chat.py** - 统一聊天接口，整合多种对话模式
- **test_research_mode.py** - 研究模式测试文件
- **__init__.py** - 包初始化文件

#### chat/core/ - 核心逻辑
- **chat.py** - 聊天核心实现
- **unified_agent.py** - 统一 Agent 实现，整合多个工具和能力
- **session_manager.py** - 会话管理器，处理对话上下文
- **__init__.py** - 包初始化文件

#### chat/tools/ - 工具集
- **web_tools.py** - Web 搜索工具
- **web_tools_with_auth.py** - 带认证的 Web 工具
- **kb_tools.py** - 知识库工具
- **kb_config.py** - 知识库配置
- **__init__.py** - 包初始化文件

#### chat/config/ - 配置管理
- **system_prompts.py** - 系统提示词配置
- **agent_config.py** - Agent 配置
- **web_platform_config.py** - Web 平台配置
- **__init__.py** - 包初始化文件

### muti/ 子目录 - 多模态合成组件
- **helloworld.py** - 示例文件
- **synthesis_audio.py** - 音频合成功能
- **synthesis_image.py** - 图像合成功能
- **synthesis_picture.py** - 图片合成功能
- **synthesis_video.py** - 视频合成功能
- **visual_understanding.py** - 视觉理解功能
- **test_synchronicity.py** - 同步性测试
- **__init__.py** - 包初始化文件

### Data/ 子目录
- 数据存储目录

### __init__.py
- 组件包初始化文件

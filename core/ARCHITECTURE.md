# Core 目录架构说明

**⚠️ 一旦我所属的文件夹有所变化，请更新我。**

## 架构概览
核心模型层，负责模型注册管理和各类 AI 模型客户端的封装，是整个系统与外部模型服务交互的基础层。

## 文件清单

### model/ 子目录
- **model_registry.py** - 模型注册中心，统一管理和注册所有可用的模型实例

### model_client/ 子目录
- **kling_model_client/** - Kling 模型客户端模块
  - **kling_get_api.py** - Kling API 获取工具，处理 API 调用逻辑
  - **kling_video_model_client.py** - Kling 视频生成模型客户端，封装视频生成接口

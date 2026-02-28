# Workflow 目录架构说明

**⚠️ 一旦我所属的文件夹有所变化，请更新我。**

## 架构概览
工作流引擎，定义活动和任务组，编排复杂的视频处理流程。

## 文件清单

### activity/ 子目录 - 活动定义
- **activity_video_reproduce_001.py** - 视频复现活动实现
- **__init__.py** - 包初始化文件

### taskgroup/ 子目录 - 任务组定义
- **taskgroup_video_reproduce.py** - 视频复现任务组，组织多个活动
- **__init__.py** - 包初始化文件

### __init__.py
- 工作流包初始化文件

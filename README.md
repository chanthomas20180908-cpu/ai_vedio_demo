# pythonProject - AI视频Demo项目

## ⚠️ 文档更新规则（强制执行）

**任何功能、架构、写法更新完成后，必须更新相关目录的子文档！**

- 修改代码文件时 → 更新文件头部注释（Input/Output/Pos）
- 修改文件夹结构时 → 更新该文件夹的 ARCHITECTURE.md
- 修改系统架构时 → 更新本 README.md 和相关子目录文档

## 项目整体架构

本项目是一个基于 AI 的视频处理和多模态交互系统，主要模块如下：

### 核心目录结构

- **core/** - 核心模型层，包含模型注册和各类模型客户端
- **component/** - 组件层，包含聊天、多模态交互等功能组件
- **workflow/** - 工作流引擎，定义活动和任务组
- **agent/** - AI Agent 实现
- **config/** - 配置文件目录
- **utils/** / **util/** - 工具函数库
- **test/** - 测试文件和测试用例
- **gradio/** - Gradio Web 界面
- **examples/** - 示例代码
- **data/** - 数据存储目录
- **debug/** - 调试相关文件
- **env/** - 环境配置

### 文档组织规范

1. 每个子目录包含 `ARCHITECTURE.md` 文件，记录该目录的架构说明
2. 每个 Python 文件开头包含三行注释：Input、Output、Pos
3. 所有文档都包含自更新提醒

详细架构请参考各子目录的 `ARCHITECTURE.md` 文件。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 查看各模块文档
cat core/ARCHITECTURE.md
cat component/ARCHITECTURE.md
cat workflow/ARCHITECTURE.md
```

## 开发约定

- Python 版本：3.x
- 代码风格：PEP 8
- 文档语言：中文

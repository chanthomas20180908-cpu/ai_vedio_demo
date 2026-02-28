#!/usr/bin/env python3
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: OSS 认证信息
Output: OSS 配置对象
Pos: 对象存储配置管理
"""

"""
OSS配置模块
引用My_files项目的OSS配置
"""

import os

# My_files项目路径
MY_FILES_PATH = "/Users/thomaschan/Code/My_files"

# OSS配置文件路径
OSS_ENV_PATH = os.path.join(MY_FILES_PATH, "env/default.env")

# OSS记录文件路径
OSS_RECORDS_DIR = os.path.join(MY_FILES_PATH, "oss_records")

# OSS文件基础路径
OSS_MULTIMEDIA_BASE = "my_multimedia"
OSS_IMAGES_BASE = f"{OSS_MULTIMEDIA_BASE}/my_images"
OSS_VIDEOS_BASE = f"{OSS_MULTIMEDIA_BASE}/my_videos"
OSS_AUDIOS_BASE = f"{OSS_MULTIMEDIA_BASE}/my_audios"

# 默认URL过期时间(秒)
DEFAULT_URL_EXPIRE_SECONDS = 3600  # 1小时


def get_oss_path(local_relative_path: str) -> str:
    """
    将本地相对路径转换为OSS路径
    
    Args:
        local_relative_path: 本地相对路径,如 'my_images/slave/test.png'
    
    Returns:
        OSS完整路径,如 'my_multimedia/my_images/slave/test.png'
    """
    # 如果已经包含my_multimedia前缀,直接返回
    if local_relative_path.startswith(OSS_MULTIMEDIA_BASE):
        return local_relative_path
    
    # 否则添加前缀
    return f"{OSS_MULTIMEDIA_BASE}/{local_relative_path}"


def get_local_oss_path_from_old_path(old_local_path: str) -> str:
    """
    从旧的本地完整路径提取OSS路径
    
    Args:
        old_local_path: 旧的本地路径,如 '/Users/thomaschan/Code/My_files/my_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png'
    
    Returns:
        OSS路径,如 'my_multimedia/my_images/slave/wan25_t2i_1765248811.png'
    """
    # 查找my_multimedia的位置
    if "my_multimedia" in old_local_path:
        idx = old_local_path.find("my_multimedia")
        return old_local_path[idx:]
    
    # 如果没找到,尝试查找my_files后的路径
    if "my_files/" in old_local_path:
        parts = old_local_path.split("my_files/")
        if len(parts) > 1:
            relative = parts[1]
            # 移除可能的my_multimedia前缀重复
            if not relative.startswith("my_multimedia"):
                return f"my_multimedia/{relative}"
            return relative
    
    # 无法识别,返回原路径
    return old_local_path


if __name__ == "__main__":
    # 测试路径转换
    test_paths = [
        "/Users/thomaschan/Code/My_files/my_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png",
        "my_images/slave/test.png",
        "my_multimedia/my_images/test.png"
    ]
    
    print("测试路径转换:")
    for path in test_paths:
        oss_path = get_local_oss_path_from_old_path(path)
        print(f"{path}")
        print(f"  -> {oss_path}\n")

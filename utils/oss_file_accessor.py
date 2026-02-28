#!/usr/bin/env python3
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: OSS路径、OSSManager实例
Output: 文件URL、本地临时文件路径
Pos: OSS文件访问统一接口
"""

"""
OSS文件访问器
提供统一的OSS文件访问接口,自动处理URL过期刷新和临时下载
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict
import tempfile
import requests
from datetime import datetime

# 添加My_files路径到系统路径
MY_FILES_PATH = "/Users/thomaschan/Code/My_files"
if MY_FILES_PATH not in sys.path:
    sys.path.insert(0, MY_FILES_PATH)

from oss_manager import OSSManager


class OSSFileAccessor:
    """OSS文件访问器"""
    
    def __init__(self, oss_manager: Optional[OSSManager] = None):
        """
        初始化OSS访问器
        
        Args:
            oss_manager: OSS管理器实例,如果为None则自动创建
        """
        if oss_manager is None:
            # 使用My_files的环境配置
            env_path = os.path.join(MY_FILES_PATH, "env/default.env")
            self.oss_manager = OSSManager.from_env(env_path)
        else:
            self.oss_manager = oss_manager
        
        # 临时文件缓存目录
        self.temp_cache_dir = Path(tempfile.gettempdir()) / "pythonProject_oss_cache"
        self.temp_cache_dir.mkdir(exist_ok=True)
    
    def get_file_url(self, oss_path: str, auto_refresh: bool = True, 
                     expire_seconds: int = 3600) -> Optional[str]:
        """
        获取OSS文件的访问URL,自动处理过期刷新
        
        Args:
            oss_path: OSS文件路径,如 'my_multimedia/my_images/test.png'
            auto_refresh: 是否自动刷新过期的URL
            expire_seconds: URL过期时间(秒),默认1小时
        
        Returns:
            可访问的URL,如果文件不存在返回None
        """
        # 检查文件是否存在于OSS
        if not self.oss_manager.file_exists(oss_path):
            print(f"文件不存在于OSS: {oss_path}")
            return None
        
        # 尝试从映射记录中获取URL
        url_info = self.oss_manager.get_file_url(oss_path, refresh=auto_refresh)
        
        if url_info:
            # 检查是否过期
            if url_info.get('is_public'):
                return url_info['url']
            
            if url_info.get('expires_at'):
                expires_at = datetime.fromisoformat(url_info['expires_at'])
                if datetime.now() < expires_at:
                    return url_info['url']
        
        # 如果没有记录或已过期,生成新的签名URL
        print(f"生成新的签名URL: {oss_path}")
        url = self.oss_manager.get_signed_url(oss_path, expire_seconds)
        
        # 更新URL映射
        url_mappings = self.oss_manager.load_url_mappings()
        from datetime import timedelta
        url_mappings[oss_path] = {
            'url': url,
            'expires_at': (datetime.now() + timedelta(seconds=expire_seconds)).isoformat(),
            'is_public': False
        }
        self.oss_manager.save_url_mappings(url_mappings)
        
        return url
    
    def download_to_temp(self, oss_path: str, use_cache: bool = True) -> Optional[str]:
        """
        从OSS下载文件到临时目录
        
        Args:
            oss_path: OSS文件路径
            use_cache: 是否使用缓存(如果本地已有则不重复下载)
        
        Returns:
            本地临时文件路径,失败返回None
        """
        # 生成本地缓存路径
        cache_file = self.temp_cache_dir / oss_path.replace("/", "_")
        
        # 如果使用缓存且文件已存在
        if use_cache and cache_file.exists():
            print(f"使用缓存文件: {cache_file}")
            return str(cache_file)
        
        # 获取URL
        url = self.get_file_url(oss_path)
        if not url:
            return None
        
        # 下载文件
        try:
            print(f"从OSS下载: {oss_path}")
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            
            # 保存到临时文件
            cache_file.write_bytes(response.content)
            print(f"下载成功: {cache_file}")
            return str(cache_file)
        
        except Exception as e:
            print(f"下载失败: {oss_path}, 错误: {e}")
            return None
    
    def get_file_info(self, oss_path: str) -> Optional[Dict]:
        """
        获取OSS文件信息
        
        Args:
            oss_path: OSS文件路径
        
        Returns:
            文件信息字典
        """
        return self.oss_manager.get_remote_file_info(oss_path)
    
    def file_exists(self, oss_path: str) -> bool:
        """
        检查文件是否存在于OSS
        
        Args:
            oss_path: OSS文件路径
        
        Returns:
            是否存在
        """
        return self.oss_manager.file_exists(oss_path)
    
    def clear_cache(self):
        """清空临时缓存目录"""
        import shutil
        if self.temp_cache_dir.exists():
            shutil.rmtree(self.temp_cache_dir)
            self.temp_cache_dir.mkdir(exist_ok=True)
            print(f"已清空缓存目录: {self.temp_cache_dir}")


# 全局单例
_global_accessor = None


def get_oss_accessor() -> OSSFileAccessor:
    """获取全局OSS访问器实例"""
    global _global_accessor
    if _global_accessor is None:
        _global_accessor = OSSFileAccessor()
    return _global_accessor


# 便捷函数
def get_oss_url(oss_path: str, auto_refresh: bool = True) -> Optional[str]:
    """获取OSS文件URL的便捷函数"""
    accessor = get_oss_accessor()
    return accessor.get_file_url(oss_path, auto_refresh)


def download_oss_file(oss_path: str, use_cache: bool = True) -> Optional[str]:
    """下载OSS文件到本地临时目录的便捷函数"""
    accessor = get_oss_accessor()
    return accessor.download_to_temp(oss_path, use_cache)


if __name__ == "__main__":
    # 测试代码
    accessor = OSSFileAccessor()
    
    # 测试URL获取
    test_path = "my_multimedia/my_images/slave/wan25_t2i_1765248811.png"
    url = accessor.get_file_url(test_path)
    print(f"\n测试URL获取:")
    print(f"文件: {test_path}")
    print(f"URL: {url}")
    
    # 测试文件下载
    local_path = accessor.download_to_temp(test_path)
    print(f"\n测试文件下载:")
    print(f"本地路径: {local_path}")

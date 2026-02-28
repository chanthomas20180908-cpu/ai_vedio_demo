#!/usr/bin/env python3
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_oss_integration.py
"""

"""
OSS集成测试脚本
测试OSS访问器的各项功能(需要先配置OSS)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.oss_file_accessor import OSSFileAccessor, get_oss_url, download_oss_file
from config.oss_config import get_local_oss_path_from_old_path


def test_path_conversion():
    """测试路径转换功能"""
    print("="*60)
    print("测试1: 路径转换")
    print("="*60)
    
    test_paths = [
        "/Users/thomaschan/Code/My_files/my_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png",
        "my_multimedia/my_images/test.png",
        "my_images/test.png"
    ]
    
    for old_path in test_paths:
        oss_path = get_local_oss_path_from_old_path(old_path)
        print(f"\n原路径: {old_path}")
        print(f"OSS路径: {oss_path}")
    
    print("\n✅ 路径转换测试完成\n")


def test_oss_accessor():
    """测试OSS访问器(需要真实配置)"""
    print("="*60)
    print("测试2: OSS访问器功能")
    print("="*60)
    
    try:
        # 创建访问器
        print("\n初始化OSS访问器...")
        accessor = OSSFileAccessor()
        print("✅ OSS访问器初始化成功")
        
        # 测试文件路径
        test_file = "my_multimedia/my_images/slave/wan25_t2i_1765248811.png"
        
        # 检查文件是否存在
        print(f"\n检查文件是否存在: {test_file}")
        if accessor.file_exists(test_file):
            print("✅ 文件存在于OSS")
            
            # 获取文件信息
            print("\n获取文件信息...")
            info = accessor.get_file_info(test_file)
            if info:
                print(f"  文件大小: {info['size']} bytes ({info['size']/1024/1024:.2f} MB)")
                print(f"  Content-Type: {info.get('content_type', 'N/A')}")
                print(f"  最后修改: {info.get('last_modified', 'N/A')}")
            
            # 获取URL
            print("\n获取访问URL...")
            url = accessor.get_file_url(test_file, expire_seconds=3600)
            if url:
                print(f"✅ URL获取成功")
                print(f"  URL: {url[:100]}...")
            
            # 测试下载
            print("\n测试文件下载...")
            local_path = accessor.download_to_temp(test_file, use_cache=True)
            if local_path:
                print(f"✅ 文件下载成功")
                print(f"  本地路径: {local_path}")
                
                # 验证文件大小
                import os
                local_size = os.path.getsize(local_path)
                print(f"  本地文件大小: {local_size} bytes")
            
            # 测试缓存机制
            print("\n测试缓存机制(再次下载)...")
            local_path2 = accessor.download_to_temp(test_file, use_cache=True)
            if local_path2:
                print(f"✅ 使用缓存: {local_path2}")
        
        else:
            print("❌ 文件不存在于OSS")
            print("请先上传文件或修改测试文件路径")
        
        print("\n✅ OSS访问器测试完成")
    
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("\n请先按照 OSS_SETUP.md 配置OSS:")
        print("1. cd /Users/thomaschan/Code/My_files")
        print("2. cp env/default.env.example env/default.env")
        print("3. 编辑 env/default.env 填写OSS配置")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_convenience_functions():
    """测试便捷函数"""
    print("\n" + "="*60)
    print("测试3: 便捷函数")
    print("="*60)
    
    try:
        test_file = "my_multimedia/my_images/slave/wan25_t2i_1765248811.png"
        
        print(f"\n使用便捷函数获取URL: {test_file}")
        url = get_oss_url(test_file)
        if url:
            print(f"✅ URL: {url[:80]}...")
        
        print(f"\n使用便捷函数下载文件: {test_file}")
        local_path = download_oss_file(test_file)
        if local_path:
            print(f"✅ 本地路径: {local_path}")
        
        print("\n✅ 便捷函数测试完成")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    print("\n🚀 开始OSS集成测试\n")
    
    # 测试1: 路径转换(无需配置)
    # test_path_conversion()
    
    # 测试2: OSS访问器(需要配置)
    test_oss_accessor()
    
    # 测试3: 便捷函数(需要配置)
    test_convenience_functions()
    
    print("\n" + "="*60)
    print("🎉 所有测试完成")
    print("="*60)

"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：run_mvp_i2v_test.py
"""

"""
MVP测试脚本: 运行3个最佳表情包提示词
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.test_prompt_mvp import (
    TEST_I2V_PROMPT_STEAM_RAGE,
    TEST_I2V_PROMPT_SAD_CRY,
    TEST_I2V_PROMPT_GLITCH,
    TEST_I2V_PROMPT_EXAGGERATED_CRY,
    TEST_I2V_PROMPT_ZEN_HELPLESS,
    TEST_I2V_PROMPT_ZEN_MONK,
    TEST_I2V_PROMPT_CONTEMPT
)
from debug.debug_sync_i2v_3mdls import debug_sync_i2v_mdls
from config.logging_config import setup_logging, get_logger
from config.oss_config import get_local_oss_path_from_old_path
import time

# OSS图片路径(不再使用本地路径)
# 原本地路径: /Users/thomaschan/Code/My_files/my_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png
# oss_image_path = "/Users/thomaschan/Downloads/download_paul.png"  # 保罗
oss_image_path_000 = '/Users/thomaschan/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/download_paul.png'  # 保罗
oss_image_path_001 = '/Users/thomaschan/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/download_23424.png'  # 宝玉
oss_image_path_002 = '/Users/thomaschan/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/wan25_t2i_1765358732.png'  # man 1
oss_image_path_003 = '/Users/thomaschan/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/wan25_t2i_1765358774.png'  # man 2
oss_image_path_004 = '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/NBA/download_tailunlu.png'  # 卢指导

# hack csy 20251220:临时先用本地路径跑
# i_path_test = oss_image_path

# # 从OSS下载到临时目录(自动缓存)
# print(f"从OSS获取图片: {oss_image_path}")
# i_path_test = download_oss_file(oss_image_path)
# if not i_path_test:
#     raise RuntimeError(f"无法从OSS获取文件: {oss_image_path}")
# print(f"本地临时路径: {i_path_test}")

def run_mvp_test():
    """运行MVP测试"""
    setup_logging()
    logger = get_logger(__name__)
    
    # 定义7个测试集
    test_sets = [
        {
            "name": "蒸汽喷发式暴怒",
            "image_path": oss_image_path_002,
            "prompt": TEST_I2V_PROMPT_STEAM_RAGE
        },
        {
            "name": "委屈大哭",
            "image_path": oss_image_path_004,
            "prompt": TEST_I2V_PROMPT_SAD_CRY
        },
        {
            "name": "表情包格式崩坏",
            "image_path": oss_image_path_003,
            "prompt": TEST_I2V_PROMPT_GLITCH
        },
        {
            "name": "夸张大哭泪流成河",
            "image_path": oss_image_path_002,
            "prompt": TEST_I2V_PROMPT_EXAGGERATED_CRY
        },
        # {
        #     "name": "佛系无奈看破红尘",
        #     "image_path": oss_image_path_002,
        #     "prompt": TEST_I2V_PROMPT_ZEN_HELPLESS
        # },
        {
            "name": "真我佛系与世无争",
            "image_path": oss_image_path_001,
            "prompt": TEST_I2V_PROMPT_ZEN_MONK
        },
        {
            "name": "极致鄙夷与不屑",
            "image_path": oss_image_path_003,
            "prompt": TEST_I2V_PROMPT_CONTEMPT
        }
    ]
    
    # 要运行的模型
    enabled_models = [
        "wan-2.2-i2v-plus",
        "doubao-seedance-1-lite",
        "MiniMax-Hailuo-02"
    ]
    
    all_results = []
    total_start_time = time.time()
    
    logger.info("="*60)
    logger.info("开始MVP测试: 7个提示词 × 3个模型 = 21个视频")
    logger.info("="*60)
    
    for idx, test_set in enumerate(test_sets, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"测试 {idx}/7: {test_set['name']}")
        logger.info(f"{'='*60}")
        
        test_start_time = time.time()
        
        results = debug_sync_i2v_mdls(
            image_path=test_set["image_path"],
            prompt=test_set["prompt"],
            enabled_models=enabled_models
        )
        
        test_end_time = time.time()
        test_duration = test_end_time - test_start_time
        
        logger.info(f"\n{test_set['name']} 完成，耗时: {test_duration:.2f}秒")
        logger.info("-"*60)
        for result in results:
            logger.info(f"模型: {result['model']}")
            logger.info(f"视频URL: {result.get('video_url', 'N/A')}")
            logger.info(f"视频路径: {result.get('video_path', 'N/A')}")
            logger.info(f"耗时: {result.get('time_calculate', 'N/A')}")
            logger.info("-"*40)
        
        all_results.append({
            "test_name": test_set['name'],
            "duration": test_duration,
            "results": results
        })
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # 输出总结
    logger.info("\n" + "="*60)
    logger.info("MVP测试完成!")
    logger.info("="*60)
    logger.info(f"总耗时: {total_duration:.2f}秒 ({total_duration/60:.2f}分钟)")
    logger.info(f"共生成视频数: {sum(len(r['results']) for r in all_results)}个")
    
    logger.info("\n详细结果:")
    for idx, test_result in enumerate(all_results, 1):
        logger.info(f"\n{idx}. {test_result['test_name']} (耗时: {test_result['duration']:.2f}秒)")
        for model_result in test_result['results']:
            logger.info(f"   - {model_result['model']}: {model_result.get('time_calculate', 'N/A')}")
    
    return all_results


if __name__ == "__main__":
    results = run_mvp_test()
    print("\n✅ MVP测试执行完成!")
    print(f"生成视频总数: {sum(len(r['results']) for r in results)}个")

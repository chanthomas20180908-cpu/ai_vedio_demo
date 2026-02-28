"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_sync_i2v_3mdls.py
"""

from data.test_prompt import TEST_I2V_PROMPT_019, TEST_I2V_PROMPT_005, TEST_I2V_PROMPT_007, TEST_I2V_PROMPT_006, \
    TEST_I2V_PROMPT_008, TEST_I2V_PROMPT_009, TEST_I2V_PROMPT_013, TEST_I2V_PROMPT_017, TEST_I2V_PROMPT_018, \
    TEST_I2V_PROMPT_016, TEST_I2V_PROMPT_020, TEST_I2V_PROMPT_020, TEST_I2V_PROMPT_020, TEST_I2V_PROMPT_020, TEST_I2V_PROMPT_035
import data.test_prompt as ppt
from config.logging_config import get_logger, setup_logging
from debug.debug_sync_wan_i2v import debug_synx_i2v_wan22
from test.test_i2v_doubao import debug_seedance_i2v
from test.test_i2v_minimax import debug_minimax_i2v
from util.util_url import upload_file_to_oss

import time
from typing import Callable, Dict, List, Tuple, Optional

i_path_1 = "/Users/test/Code/My_files/my_multimedia/my_images/baby/wan25_t2i_1764748796.png"  # baby 1
i_path_2 = "/Users/test/Code/My_files/my_multimedia/my_images/baby/wan25_t2i_1764749118.png"  # baby 2
i_path_3 = "/Users/test/Code/My_files/my_multimedia/my_images/baby/wan25_t2i_1764749157.png"  # baby 3
i_path_4 = "/Users/test/Code/My_files/my_multimedia/my_images/baby/wan25_t2i_1764749197.png"  # baby 4

i_path_5 = "/Users/test/Code/My_files/my_multimedia/my_images/欠男/wan25_t2i_1764831129.png"  # 欠男
i_path_5_1 = "/Users/test/code/My_files/my_multimedia/my_images/slave/wan25_t2i_1765248733.png"  # 社畜女 1

i_path_6 = "/Users/test/code/My_files/my_multimedia/my_images/slave/wan25_t2i_1765247834.png"  # 社畜男 1
i_path_7 = "/Users/test/code/My_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png"  # 社畜女 1

i_path_8 = '/Users/test/code/My_files/my_multimedia/my_images/1:1_girl_image/wan25_t2i_1765263759.png'  # 短发 1
i_path_9 = '/Users/test/code/My_files/my_multimedia/my_images/1:1_girl_image/wan25_t2i_1765263603.png'
i_path_10 = '/Users/test/code/My_files/my_multimedia/my_images/1:1_girl_image/wan25_t2i_1765263886.png'

i_path_11 = '/Users/test/code/My_files/my_multimedia/my_images/动物/wan25_t2i_1765357868.png'  # 橘猫
i_path_12 = '/Users/test/code/My_files/my_multimedia/my_images/虚拟人物/wan25_t2i_1765358682.png'  # mengnalisha
i_path_13 = '/Users/test/code/My_files/my_multimedia/my_images/虚拟人物/wan25_t2i_1765358869.png'  # 奥特曼
i_path_14 = '/Users/test/code/My_files/my_multimedia/my_images/虚拟人物/tetet.png'  # 猪迪
i_path_15 = '/Users/test/code/My_files/my_multimedia/my_images/虚拟人物/wan25_t2i_1765358641.png'  # 财神
i_path_16 = "/Users/test/code/My_files/my_multimedia/my_images/fu_mam/wan25_t2i_1765433853.png"  # 红老头
i_path_17 = '/Users/test/code/My_files/my_multimedia/my_images/fu_mam/wan25_t2i_1765433509.png'  # 红老头1

i_path_18 = '/Users/test/code/My_files/my_multimedia/my_images/猫猫/wan25_t2i_1765521799.png'  # 喜庆胖橘
i_path_19 = '/Users/test/code/My_files/my_multimedia/my_images/猫猫/wan25_t2i_1765521764.png'  # 社畜奶牛猫
i_path_20 = '/Users/test/code/My_files/my_multimedia/my_images/猫猫/wan25_t2i_1765522145.png'  #  老板蓝猫
i_path_21 = '/Users/test/code/My_files/my_multimedia/my_images/猫猫/wan25_t2i_1765522551.png'  # 程序员猫
i_path_22 = '/Users/test/code/My_files/my_multimedia/my_images/猫猫/wan25_t2i_1765522420.png'  # 布偶猫
i_path_23 = '/Users/test/code/My_files/my_multimedia/my_images/猫猫/eraedsa.png'  # 下雪北京布偶猫

i_path_24 = '/Users/test/code/My_files/my_multimedia/my_images/西游/36y8J8s18etjgXGnDo6LdGZqQ7I.png'  # 悟空

i_path_30 = '/Users/test/code/My_files/my_multimedia/my_images/红楼/download_3243213.png'  # 黛玉
i_path_29 = '/Users/test/code/My_files/my_multimedia/my_images/红楼/download_23424.png'  # 宝玉

i_path_31 = '/Users/test/code/My_files/my_multimedia/my_images/NBA/download_jordan_001.png'  # 乔丹
i_path_32 = '/Users/test/code/My_files/my_multimedia/my_images/NBA/download_james_001.png'  # 詹姆斯
i_path_33 = '/Users/test/code/My_files/my_multimedia/my_images/NBA/download_curry_001.png'
i_path_34 = '/Users/test/code/My_files/my_multimedia/my_images/NBA/download_kobe_001.png'


test_set_1 = {
    #  宝宝动画火焰
    "image_path": i_path_1,
    "prompt": ppt.TEST_I2V_PROMPT_005
}
test_set_2 = {
    #  宝宝彩虹光束
    "image_path": i_path_2,
    "prompt": ppt.TEST_I2V_PROMPT_006
}
test_set_3 = {
    #  宝宝吃柠檬
    "image_path": i_path_4,
    "prompt": ppt.TEST_I2V_PROMPT_007
}
test_set_4 = {
    #  欠男扇巴掌

    "image_path": i_path_5,
    "prompt": ppt.TEST_I2V_PROMPT_008
}
test_set_5 = {
    #  欠男淋水

# --- 结果 ---  minimax
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765419528.mp4
# 耗时: 121.4009 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343518217072835.mp4
# 耗时: 51.3122 秒
# ----------------------------------------

    # "image_path": i_path_5,
"image_path": i_path_24,
    "prompt": ppt.TEST_I2V_PROMPT_009_001
}
# test_set_5_1 = {
#     #  风控挑战
#
#     "image_path": i_path_5,
#     "prompt": ppt.TEST_I2V_PROMPT_010
# }
test_set_6 = {
    #  数字气球跨年
    "image_path": i_path_6,
    "prompt": ppt.TEST_I2V_PROMPT_013
}
test_set_7 = {
    #  天降圣诞帽
    "image_path": i_path_8,
    "prompt": ppt.TEST_I2V_PROMPT_017
}
test_set_8 = {
    #  拐杖糖
    "image_path": i_path_9,
    "prompt": ppt.TEST_I2V_PROMPT_018
}
test_set_9 = {
    #  红包金
# minimax
#     模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan25_video_1765335414.mp4
# 耗时: 23.2174 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210105719.mp4
# 耗时: 24.5869 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343171554963754.mp4
# 耗时: 61.6268 秒

    "image_path": i_path_10,
    "prompt": ppt.TEST_I2V_PROMPT_016
}
test_set_10 = {
    #  CPU爆炸

#     模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan25_video_1765335929.mp4
# 耗时: 27.8788 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210110551.mp4
# 耗时: 21.9914 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343175879127234.mp4
# 耗时: 61.5283 秒
# ----------------------------------------
# minimax
# minimax_i2v_343173641195834.mp4
# doubao-seedance-1-0-pro-250528_result20251210111702.mp4
# doubao-seedance-1-0-lite-i2v-250428_result20251210111621.mp4
# wan25_video_1765336561.mp4

    "image_path": i_path_19,
    "prompt": ppt.TEST_I2V_PROMPT_020
}
# test_set_11 = {
#     #  跨年2
#     "image_path": i_path_7,
#     "prompt": ppt.TEST_I2V_PROMPT_021
# }
test_set_12 = {
    #  跨年3
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan25_video_1765337238.mp4
# 耗时: 27.8715 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210112741.mp4
# 耗时: 22.1888 秒
# ----------------------------------------
# 模型: doubao-seedance-1-pro
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-pro-250528_result20251210112828.mp4
# 耗时: 46.9068 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343175543742781.mp4
# 耗时: 71.7218 秒
# ----------------------------------------

# --- 结果 ---  wan
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765341255.mp4
# 耗时: 28.3772 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210123441.mp4
# 耗时: 25.4270 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343194409701593.mp4
# 耗时: 51.1467 秒
# ----------------------------------------

    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_022
}
test_set_13 = {
    #  跨年4
    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_023
}
test_set_14 = {
    #  跨年5
    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_024
}
test_set_15 = {
    #  跨年6

# -- 结果 --- seedance
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765341474.mp4
# 耗时: 22.9392 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210123816.mp4
# 耗时: 21.8946 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343191654273192.mp4
# 耗时: 41.0879 秒
# ----------------------------------------

    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_030
}
test_set_16 = {
    #  跨年7
    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_031
}
# test_set_18 = {
#     #  跨年9
#     "image_path": i_path_7,
#     "prompt": ppt.TEST_I2V_PROMPT_032
# }
test_set_19 = {
    #  跨年10
    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_033
}
test_set_20 = {
    #  跨11
# --- 结果 --- minimax
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765342349.mp4
# 耗时: 23.7636 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210125251.mp4
# 耗时: 21.2451 秒
# ----------------------------------------
# 模型: doubao-seedance-1-pro
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-pro-250528_result20251210125330.mp4
# 耗时: 39.3787 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343196872388818.mp4
# 耗时: 41.0381 秒
# ----------------------------------------
    "image_path": i_path_9,
    "prompt": ppt.TEST_I2V_PROMPT_034
}

test_set_21 = {
    #  圣诞1
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765349200.mp4
# 耗时: 28.0594 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210144659.mp4
# 耗时: 19.0343 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343228627529995.mp4
# 耗时: 51.3545 秒
# ----------------------------------------
    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_040
}
test_set_22 = {
    #  圣诞2 圣诞树跳舞
# --- 结果 ---  wan / minimax
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765349706.mp4
# 耗时: 23.0826 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210145527.mp4
# 耗时: 20.0338 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343228551377120.mp4
# 耗时: 41.1573 秒
# ----------------------------------------
    "image_path": i_path_11,
    "prompt": ppt.TEST_I2V_PROMPT_041
}
test_set_23 = {
    #  圣诞3 圣诞卡在烟囱
# --- 结果 --- minimax/seedance
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765350030.mp4
# 耗时: 28.5398 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210150223.mp4
# 耗时: 112.2664 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343229999583473.mp4
# 耗时: 72.4377 秒
# ----------------------------------------

    "image_path": i_path_2,
    "prompt": ppt.TEST_I2V_PROMPT_042
}
test_set_24 = {
    #  圣诞4
#
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765350594.mp4
# 耗时: 22.8848 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251210151021.mp4
# 耗时: 26.0631 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343233381888224.mp4
# 耗时: 41.2112 秒
# ----------------------------------------

    "image_path": i_path_3,
    "prompt": ppt.TEST_I2V_PROMPT_043
}
test_set_25 = {
    # 钞票池
    "image_path": i_path_5_1,
    "prompt": ppt.TEST_I2V_PROMPT_050
}
test_set_26 = {
    # 耳光风暴
    "image_path": i_path_7,
    "prompt": ppt.TEST_I2V_PROMPT_051
}
test_set_27 = {
    # 键盘粉碎
    "image_path": i_path_5_1,
    "prompt": ppt.TEST_I2V_PROMPT_052
}
# test_set_28 = {
#     # 元宝
# # --- 结果 ---
# # 模型: doubao-seedance-1-lite
# # 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251211140251.mp4
# # 耗时: 66.8871 秒
# # ----------------------------------------
# # 模型: MiniMax-Hailuo-02
# # 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343569911726372.mp4
# # 耗时: 51.3885 秒
# # ----------------------------------------
#     "image_path": i_path_15,
#     "prompt": ppt.TEST_I2V_PROMPT_053
# }
test_set_29 = {
    # 福寿双全
    "image_path": i_path_15,
    "prompt": ppt.TEST_I2V_PROMPT_054
}
test_set_30 = {
    # 金蛇纳财
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765436644.mp4
# 耗时: 28.4392 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251211150449.mp4
# 耗时: 44.1124 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343584335909046.mp4
# 耗时: 51.2369 秒
# ----------------------------------------
    "image_path": i_path_16,
    "prompt": ppt.TEST_I2V_PROMPT_055
}
test_set_31 = {
    # 红运当头
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251211152746.mp4
# 耗时: 22.9880 秒
    "image_path": i_path_17,
    "prompt": ppt.TEST_I2V_PROMPT_056
}

test_set_32 = {
    # 下雪1
# --- 结果 ---
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343935484252392.mp4
# 耗时: 41.1300 秒
    "image_path": i_path_18,
    "prompt": ppt.TEST_I2V_PROMPT_060
}
test_set_33 = {
    # 下雪2
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765522499.mp4
# 耗时: 23.3415 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251212145521.mp4
# 耗时: 21.0795 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343937850151203.mp4
# 耗时: 51.1571 秒
# ----------------------------------------
# token_calculate 运行时间: 96.0551 秒
    "image_path": i_path_18,
    "prompt": ppt.TEST_I2V_PROMPT_061
}

test_set_34 = {
    # 下雪水晶球
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1765524163.mp4
# 耗时: 147.1549 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: None
# 耗时: 2.7217 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_343943411884343.mp4
# 耗时: 51.1313 秒
# ----------------------------------------
    "image_path": i_path_23,
    "prompt": ppt.TEST_I2V_PROMPT_062
}

test_set_35 = {
    # 落雪
    "image_path": i_path_12,
    "prompt": ppt.TEST_I2V_PROMPT_063
}
test_set_36 = {
    # 雪杖
    "image_path": i_path_14,
    "prompt": ppt.TEST_I2V_PROMPT_064
}
test_set_37 = {
    # 刀人
    ## 效果一般
    "image_path": i_path_30,
    "prompt": ppt.TEST_I2V_PROMPT_065
}

test_set_39= {
    # 变发型
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1766056949.mp4
# 耗时: 23.2678 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_346123075608878.mp4
# 耗时: 61.2464 秒
# ----------------------------------------
    "image_path": i_path_24,
    "prompt": ppt.TEST_I2V_PROMPT_067
}
test_set_40= {
    # 长出头发
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1766058232.mp4
# 耗时: 23.7823 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251218194431.mp4
# 耗时: 38.4430 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_346127460372700.mp4
# 耗时: 61.4369 秒
# ----------------------------------------
    "image_path": i_path_31,
    "prompt": ppt.TEST_I2V_PROMPT_068
}
test_set_41= {
    # 自戴皇冠
# --- 结果 ---
# 模型: wan-2.2-i2v-plus
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/wan2.2-i2v-plus_1766061045.mp4
# 耗时: 23.0867 秒
# ----------------------------------------
# 模型: doubao-seedance-1-lite
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/doubao-seedance-1-0-lite-i2v-250428_result20251218203153.mp4
# 耗时: 66.4954 秒
# ----------------------------------------
# 模型: MiniMax-Hailuo-02
# 视频路径: /Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/video_results/minimax_i2v_346139746095385.mp4
# 耗时: 51.2873 秒
# ----------------------------------------
    "image_path": i_path_18,
    "prompt": ppt.TEST_I2V_PROMPT_069
}
test_set_38= {
    # 变身肌肉
    "image_path": i_path_6,
    "prompt": ppt.TEST_I2V_PROMPT_066
}
test_set_42= {
    # 变身超人
    "image_path": i_path_33,
    "prompt": ppt.TEST_I2V_PROMPT_070
}
test_set_43= {
    # 优雅崩坏
    "image_path": i_path_33,
    "prompt": ppt.TEST_I2V_PROMPT_071
}

def debug_sync_i2v_mdls(
    image_path: str,
    prompt: str,
    enabled_models: Optional[List[str]] = None,
) -> List[Dict]:
    """
    同一张图、同一条 prompt，串行跑多种 I2V 模型。

    :param image_path: 本地图片路径
    :param prompt: 文本提示词
    :param enabled_models: 要运行的模型 name 列表（见下方 model_configs 里的 'name'）。
                           为 None 或空列表时，表示跑所有模型。
    :return: 每个模型的结果列表：
             [
               {
                 "model": "wan-2.2-i2v-plus",
                 "video_url": "...",
                 "video_path": "...",
                 "time_calculate": "0.1234 秒"
               },
               ...
             ]
    """
    logger = get_logger(__name__)

    # 统一上传一次图片，所有模型复用同一个 OSS URL
    image_url = upload_file_to_oss(image_path, 300)

    video_list: List[Dict] = []

    # 定义各模型的调用配置
    model_configs: List[Dict] = [
        {
            "name": "wan-2.2-i2v-plus",
            "label": "wan 2.2 i2v",
            "timed": True,
            "run": lambda url, p: debug_synx_i2v_wan22(url, p),
        },
        {
            "name": "doubao-seedance-1-lite",
            "label": "seedance 1 lite i2v",
            "timed": True,
            "run": lambda url, p: debug_seedance_i2v(url, p, "lite"),
        },
        {
            "name": "doubao-seedance-1-pro",
            "label": "seedance 1 pro i2v",
            "timed": True,
            "run": lambda url, p: debug_seedance_i2v(url, p, "pro"),
        },
        {
            "name": "MiniMax-Hailuo-02",
            "label": "minimax i2v",
            "timed": True,
            "run": lambda url, p: debug_minimax_i2v(url, p),
        },
    ]

    # 如果传入了 enabled_models，就转成 set，方便判断
    enabled_set = set(enabled_models) if enabled_models else None

    for cfg in model_configs:
        name = cfg["name"]

        # 开关控制：如果配置了 enabled_models 且当前模型不在里面，就跳过
        if enabled_set is not None and name not in enabled_set:
            logger.info(f"跳过模型 {name}（不在 enabled_models 中）")
            continue

        label = cfg["label"]
        timed = cfg.get("timed", False)
        run_fn: Callable[[str, str], Tuple[str, str]] = cfg["run"]

        logger.info(f"----- {label} -----")
        start_time = time.time()
        video_url, video_path = run_fn(image_url, prompt)
        end_time = time.time()
        time_cal = f"{end_time - start_time:.4f} 秒"

        if timed:
            logger.info(f"{label} 运行时间: {time_cal}")

        record: Dict = {
            "model": name,
            "video_url": video_url,
            "video_path": video_path,
        }
        if timed:
            record["time_calculate"] = time_cal

        video_list.append(record)

    return video_list


if __name__ == "__main__":
    setup_logging()

    # 记录开始时间
    start_time = time.time()

    base_dir = "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/一比一角色形象图/西游"

    # 每条任务 = 1 张图 + 1 条提示词 + 1 个模型
    TASKS = [
        {
            "title": "唐僧圣诞帽",
            "image_path": f"{base_dir}/唐僧001.png",
            "prompt": ppt.TEST_I2V_PROMPT_017,
            "enabled_models": ["wan-2.2-i2v-plus"],
        },
        {
            "title": "悟空跳舞",
            "image_path": f"{base_dir}/悟空001.png",
            "prompt": ppt.TEST_I2V_PROMPT_041,
            "enabled_models": ["wan-2.2-i2v-plus"],
        },
        {
            "title": "唐僧跳舞",
            "image_path": f"{base_dir}/唐僧001.png",
            "prompt": ppt.TEST_I2V_PROMPT_041,
            "enabled_models": ["wan-2.2-i2v-plus"],
        },
        {
            "title": "八戒卡烟囱",
            "image_path": f"{base_dir}/八戒001.png",
            "prompt": ppt.TEST_I2V_PROMPT_042,
            "enabled_models": ["doubao-seedance-1-lite"],
        },
        {
            "title": "沙僧礼物核爆",
            "image_path": f"{base_dir}/沙僧001.png",
            "prompt": ppt.TEST_I2V_PROMPT_043,
            "enabled_models": ["doubao-seedance-1-lite"],
        },
    ]

    for idx, task in enumerate(TASKS, start=1):
        results = debug_sync_i2v_mdls(
            image_path=task["image_path"],
            prompt=task["prompt"],
            enabled_models=task["enabled_models"],
        )

        print(f"--- 结果 ({idx}/{len(TASKS)}) {task['title']} ---")
        for result in results:
            print(f"模型: {result['model']}")
            print(f"视频URL: {result['video_url']}")
            print(f"视频路径: {result['video_path']}")
            if 'time_calculate' in result:
                print(f"耗时: {result['time_calculate']}")
            print("-" * 40)

    # 记录结束时间并计算运行时间
    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")

"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_process_short_vedio.py
"""

import ffmpeg
from datetime import datetime
import os


def process_video_v1(input_path, output_path=None):
    """
    方案1：1.25倍速
    裁剪2.5秒（从0秒到2.5秒），然后1.25倍速 = 2秒
    保留首帧，速度变化较小
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_1.25x_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 从0秒开始裁剪2.5秒，然后1.25倍速压缩到2秒
    stream = ffmpeg.input(input_path, ss=0, t=2.5)
    stream = ffmpeg.setpts(stream, '0.8*PTS')  # 1.25倍速 = 1/1.25 = 0.8
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案1处理完成！(1.25倍速)")
    print(f"裁剪范围: 0s - 2.5s (共2.5秒，保留首帧)")
    print(f"倍速: 1.25x")
    print(f"最终时长: 2秒")
    print(f"输出路径: {output_path}")

    return output_path


def process_video_v2(input_path, output_path=None):
    """
    方案2：1.5倍速
    裁剪3秒（从0秒到3秒），然后1.5倍速 = 2秒
    保留首帧，保留更多内容
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_1.5x_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 从0秒开始裁剪3秒，然后1.5倍速压缩到2秒
    stream = ffmpeg.input(input_path, ss=0, t=3)
    stream = ffmpeg.setpts(stream, '0.67*PTS')  # 1.5倍速 = 1/1.5 ≈ 0.67
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案2处理完成！(1.5倍速)")
    print(f"裁剪范围: 0s - 3s (共3秒，保留首帧)")
    print(f"倍速: 1.5x")
    print(f"最终时长: 2秒")
    print(f"输出路径: {output_path}")

    return output_path


def process_video_v3(input_path, output_path=None):
    """
    方案3：1.75倍速
    裁剪3.5秒（从0秒到3.5秒），然后1.75倍速 = 2秒
    保留首帧，保留更多内容，速度较快
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_1.75x_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 从0秒开始裁剪3.5秒，然后1.75倍速压缩到2秒
    stream = ffmpeg.input(input_path, ss=0, t=3.5)
    stream = ffmpeg.setpts(stream, '0.57*PTS')  # 1.75倍速 = 1/1.75 ≈ 0.57
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案3处理完成！(1.75倍速)")
    print(f"裁剪范围: 0s - 3.5s (共3.5秒，保留首帧)")
    print(f"倍速: 1.75x")
    print(f"最终时长: 2秒")
    print(f"输出路径: {output_path}")

    return output_path


def process_video_v4(input_path, output_path=None):
    """
    方案4：2倍速
    裁剪4秒（从0秒到4秒），然后2倍速 = 2秒
    保留首帧，保留最多内容，速度最快
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_2.0x_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 从0秒开始裁剪4秒，然后2倍速压缩到2秒
    stream = ffmpeg.input(input_path, ss=0, t=4)
    stream = ffmpeg.setpts(stream, '0.5*PTS')  # 2倍速 = 1/2 = 0.5
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案4处理完成！(2倍速)")
    print(f"裁剪范围: 0s - 4s (共4秒，保留首帧)")
    print(f"倍速: 2.0x")
    print(f"最终时长: 2秒")
    print(f"输出路径: {output_path}")

    return output_path


def process_video_v5(input_path, output_path=None):
    """
    方案5：2.5倍速
    裁剪5秒（从0秒到5秒），然后2.5倍速 = 2秒
    保留首帧，保留全部内容，速度非常快
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_2.5x_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 从0秒开始裁剪5秒，然后2.5倍速压缩到2秒
    stream = ffmpeg.input(input_path, ss=0, t=5)
    stream = ffmpeg.setpts(stream, '0.4*PTS')  # 2.5倍速 = 1/2.5 = 0.4
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案5处理完成！(2.5倍速)")
    print(f"裁剪范围: 0s - 5s (共5秒，保留首帧)")
    print(f"倍速: 2.5x")
    print(f"最终时长: 2秒")
    print(f"输出路径: {output_path}")

    return output_path


def process_video_v6(input_path, output_path=None):
    """
    方案6：2倍速（不裁剪）
    对整个视频进行2倍速加速处理，不进行任何裁剪
    保留完整视频内容，时长减半
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_2.0x_full_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 对整个视频进行2倍速加速，不裁剪
    stream = ffmpeg.input(input_path)
    stream = ffmpeg.setpts(stream, '0.5*PTS')  # 2倍速 = 1/2 = 0.5
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案6处理完成！(2倍速，不裁剪)")
    print(f"处理范围: 整个视频（无裁剪）")
    print(f"倍速: 2.0x")
    print(f"最终时长: 原时长的50%")
    print(f"输出路径: {output_path}")

    return output_path


def process_video_v7(input_path, output_path=None):
    """
    方案7：2.5倍速（不裁剪）
    对整个视频进行2.5倍速加速处理，不进行任何裁剪
    保留完整视频内容，时长减为40%
    """
    # 如果输出路径为None，生成默认路径
    if output_path is None:
        input_dir = os.path.dirname(input_path) or '.'
        input_filename = os.path.basename(input_path)
        name, ext = os.path.splitext(input_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_2.5x_full_{timestamp}{ext}"
        output_path = os.path.join(input_dir, output_filename)

    # 对整个视频进行2.5倍速加速，不裁剪
    stream = ffmpeg.input(input_path)
    stream = ffmpeg.setpts(stream, '0.4*PTS')  # 2.5倍速 = 1/2.5 = 0.4
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    print(f"方案7处理完成！(2.5倍速，不裁剪)")
    print(f"处理范围: 整个视频（无裁剪）")
    print(f"倍速: 2.5x")
    print(f"最终时长: 原时长的40%")
    print(f"输出路径: {output_path}")

    return output_path


def process_video(input_path, output_path=None, version=1):
    """
    统一入口函数
    :param input_path: 输入视频路径
    :param output_path: 输出视频路径（可选）
    :param version: 方案版本，1、2、3、4、5、6或7
    """
    if version == 1:
        return process_video_v1(input_path, output_path)
    elif version == 2:
        return process_video_v2(input_path, output_path)
    elif version == 3:
        return process_video_v3(input_path, output_path)
    elif version == 4:
        return process_video_v4(input_path, output_path)
    elif version == 5:
        return process_video_v5(input_path, output_path)
    elif version == 6:
        return process_video_v6(input_path, output_path)
    elif version == 7:
        return process_video_v7(input_path, output_path)
    else:
        print("错误：version 只能是 1、2、3、4、5、6 或 7")
        return None


# 使用示例
if __name__ == "__main__":
    input_video = "/Users/test/code/My_files/my_files/my_vedios/XHS_Meme_results/Meme_results_20251205/wan25_video_1764924558.mp4"

    print("=" * 50)
    print("开始处理视频...")
    print("=" * 50)

    # # 方案1：1.25倍速（推荐，效果最自然）
    # print("\n【方案1】")
    # output1 = process_video(input_video, version=1)
    #
    # print("\n" + "=" * 50)
    #
    # # 方案2：1.5倍速（保留更多内容）
    # print("\n【方案2】")
    # output2 = process_video(input_video, version=2)
    #
    # print("\n" + "=" * 50)
    #
    # # 方案3：1.75倍速（保留更多内容，速度较快）
    # print("\n【方案3】")
    # output3 = process_video(input_video, version=3)
    #
    # print("\n" + "=" * 50)
    #
    # # 方案4：2倍速（保留最多内容，速度最快）
    # print("\n【方案4】")
    # output4 = process_video(input_video, version=4)
    #
    # # 方案5：2.5倍速（保留全部内容，速度非常快）
    # print("\n【方案5】")
    # output5 = process_video(input_video, version=5)

    # 方案6：2倍速（不裁剪）
    print("\n【方案6】")
    output6 = process_video(input_video, version=6)

    # 方案7：2.5倍速（不裁剪）
    print("\n【方案7】")
    output7 = process_video(input_video, version=7)

    print("\n" + "=" * 50)
    print("所有方案处理完成！")
    print("=" * 50)

"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_synchronicity.py
"""

import time
from sync import Sync
from sync.common import Audio, GenerationOptions, Video
from sync.core.api_error import ApiError


def main():
    # API配置
    api_key = "sk-RRuZvbhfTViMOdwoyGYtfQ.hqLxIbZ9l7jZ19s9NPVmqrOKzs0f4uoa"
    video_url = "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_vedios/test_vedio_man_60s_720p_silent_002.mov"
    audio_url = "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_audios/test_audio_longlaotie_v2_46s_002.mp3"

    start_time = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] 任务开始")

    client = Sync(
        base_url="https://api.sync.so",
        api_key=api_key
    ).generations

    print(f"[{time.strftime('%H:%M:%S')}] 提交唇形同步任务...")

    try:
        response = client.create(
            input=[Video(url=video_url), Audio(url=audio_url)],
            model="lipsync-2",
            options=GenerationOptions(sync_mode="cut_off"),
            output_file_name="quickstart"
        )
    except ApiError as e:
        print(f"[{time.strftime('%H:%M:%S')}] 任务提交失败: status={e.status_code}, error={e.body}")
        return

    job_id = response.id
    print(f"[{time.strftime('%H:%M:%S')}] 任务提交成功, Job ID: {job_id}")

    # 轮询状态
    poll_count = 0

    # 修正：包含所有终止状态
    TERMINAL_STATUSES = ['COMPLETED', 'FAILED', 'REJECTED']

    while True:
        poll_count += 1
        elapsed = time.time() - start_time

        print(f"[{time.strftime('%H:%M:%S')}] 检查状态 (第{poll_count}次, 已用时{elapsed:.0f}秒)...")

        try:
            generation = client.get(job_id)
            status = generation.status

            print(f"[{time.strftime('%H:%M:%S')}] 当前状态: {status}")

            # 检查是否为终止状态
            if status in TERMINAL_STATUSES:
                end_time = time.time()
                duration = end_time - start_time

                if status == 'COMPLETED':
                    print(f"\n{'=' * 50}")
                    print(f"任务完成!")
                    print(f"Job ID: {job_id}")
                    print(f"输出URL: {generation.output_url}")
                    print(f"总耗时: {duration:.2f}秒 ({duration / 60:.1f}分钟)")
                    print(f"{'=' * 50}")

                elif status == 'FAILED':
                    print(f"\n任务失败! Job ID: {job_id}")
                    print(f"耗时: {duration:.2f}秒")
                    # 尝试获取错误信息
                    if hasattr(generation, 'error'):
                        print(f"错误信息: {generation.error}")
                    if hasattr(generation, 'error_message'):
                        print(f"详细错误: {generation.error_message}")

                elif status == 'REJECTED':
                    print(f"\n任务被拒绝! Job ID: {job_id}")
                    print(f"耗时: {duration:.2f}秒")
                    if hasattr(generation, 'rejection_reason'):
                        print(f"拒绝原因: {generation.rejection_reason}")

                # 打印完整响应对象用于调试
                print(f"\n完整响应对象:")
                print(f"{generation}")

                return

            # 继续轮询的状态：PENDING, PROCESSING
            elif status in ['PENDING', 'PROCESSING']:
                print(f"状态:{status}, 等待10s")
                time.sleep(10)

            else:
                # 遇到未知状态，打印详细信息
                print(f"[警告] 未知状态: {status}")
                print(f"完整对象: {generation}")
                time.sleep(10)

        except ApiError as e:
            print(f"[{time.strftime('%H:%M:%S')}] 查询状态失败: status={e.status_code}, error={e.body}")
            time.sleep(10)

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 发生异常: {type(e).__name__}: {e}")
            # 打印详细堆栈信息用于调试
            import traceback
            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    main()

"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：update_to_aliyun.py
"""

import os

import oss2
from dotenv import load_dotenv


def main():

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))

    # 测试Qwen模型
    access_key_ = os.getenv("aliyun_access_key")
    secret_key = os.getenv("aliyun_access_secret")

    # 用你的 AccessKeyId 和 AccessKeySecret
    auth = oss2.Auth(access_key_id=access_key_, access_key_secret=secret_key)

    # 填入Bucket名称和地域节点
    bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'my-files-csy')

    # 上传文件
    bucket.put_object_from_file('music/test.mp3', '/Users/thomaschan/Code/My_files/my_files/my_vedios/test_video_man_50s_720p_silent_001.mov')

    # 上传后返回URL
    url = bucket.sign_url('GET', 'music/test.mp3', 3600)  # 有效期1小时
    print(url)


if __name__ == '__main__':
    main()
    print("上传完成")

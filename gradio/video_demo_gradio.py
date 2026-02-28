"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：video_demo_gradio.py
"""

# file: /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject/component/video_demo_gradio.py
import os
import gradio as gr
import tempfile
import requests

# 导入现有的视频生成客户端
from component import (
    test_wan22_s2v,
    test_video_retalk,
    test_liveportrait,
    test_wanx21_vace_plus
)
from config.logging_config import setup_logging
from dotenv import load_dotenv

# 初始化日志
setup_logging()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))

# 获取API密钥
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY 未配置")

# 创建临时目录用于存储上传的文件
TEMP_DIR = tempfile.mkdtemp()
print(f"临时文件目录: {TEMP_DIR}")


def save_uploaded_file(uploaded_file) -> str:
    """
    保存上传的文件到临时目录并返回文件路径

    Args:
        uploaded_file: Gradio上传的文件对象

    Returns:
        str: 保存的文件路径
    """
    if uploaded_file is None:
        return None

    file_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path


def upload_file_to_temp_server(file_path: str) -> str:
    """
    将文件上传到临时服务器并返回URL（这里模拟返回本地文件路径）
    在实际应用中，这里需要替换为真实的文件上传服务

    Args:
        file_path (str): 本地文件路径

    Returns:
        str: 文件的URL路径
    """
    # 注意：在实际应用中，这里需要将文件上传到一个公网可访问的服务器
    # 目前我们返回文件路径作为占位符
    return f"file://{file_path}"


def wan22s2v_tab():
    """万象数字人视频生成Tab"""

    def generate_video(image, audio, resolution):
        # 保存上传的文件
        image_path = save_uploaded_file(image)
        audio_path = save_uploaded_file(audio)

        if not image_path or not audio_path:
            return None, "请上传图像和音频文件"

        # 上传文件到临时服务器（模拟）
        image_url = upload_file_to_temp_server(image_path)
        audio_url = upload_file_to_temp_server(audio_path)

        # 调用视频生成函数
        try:
            video_url = test_wan22_s2v(
                DASHSCOPE_API_KEY,
                image_url=image_url,
                audio_url=audio_url,
                resolution=resolution
            )

            if video_url:
                # 下载生成的视频
                video_path = os.path.join(TEMP_DIR, f"wan22s2v_result.mp4")
                response = requests.get(video_url)
                with open(video_path, "wb") as f:
                    f.write(response.content)
                return video_path, f"视频生成成功！\n视频URL: {video_url}"
            else:
                return None, "视频生成失败"
        except Exception as e:
            return None, f"视频生成过程中出现错误: {str(e)}"

    with gr.Column():
        gr.Markdown("## 万象数字人视频生成")
        with gr.Row():
            with gr.Column():
                image_input = gr.File(label="上传人物图像", file_types=["image"])
                audio_input = gr.File(label="上传音频文件", file_types=["audio"])
                resolution_dropdown = gr.Dropdown(
                    choices=["480P", "720P", "1080P"],
                    value="480P",
                    label="视频分辨率"
                )
                generate_btn = gr.Button("生成视频")
            with gr.Column():
                video_output = gr.Video(label="生成的视频")
                status_output = gr.Textbox(label="状态信息", lines=5)

        generate_btn.click(
            fn=generate_video,
            inputs=[image_input, audio_input, resolution_dropdown],
            outputs=[video_output, status_output]
        )


def videoretalk_tab():
    """VideoRetalk视频合成Tab"""

    def synthesize_video(video, audio, ref_image, video_extension):
        # 保存上传的文件
        video_path = save_uploaded_file(video)
        audio_path = save_uploaded_file(audio)
        ref_image_path = save_uploaded_file(ref_image) if ref_image else None

        if not video_path or not audio_path:
            return None, "请上传视频和音频文件"

        # 上传文件到临时服务器（模拟）
        video_url = upload_file_to_temp_server(video_path)
        audio_url = upload_file_to_temp_server(audio_path)
        ref_image_url = upload_file_to_temp_server(ref_image_path) if ref_image_path else ""

        # 调用视频合成函数
        try:
            result_video_url = test_video_retalk(
                DASHSCOPE_API_KEY,
                video_url=video_url,
                audio_url=audio_url,
                ref_image_url=ref_image_url,
                video_extension=video_extension
            )

            if result_video_url:
                # 下载生成的视频
                result_path = os.path.join(TEMP_DIR, f"videoretalk_result.mp4")
                response = requests.get(result_video_url)
                with open(result_path, "wb") as f:
                    f.write(response.content)
                return result_path, f"视频合成成功！\n视频URL: {result_video_url}"
            else:
                return None, "视频合成失败"
        except Exception as e:
            return None, f"视频合成过程中出现错误: {str(e)}"

    with gr.Column():
        gr.Markdown("## VideoRetalk视频合成")
        with gr.Row():
            with gr.Column():
                video_input = gr.File(label="上传原始视频", file_types=["video"])
                audio_input = gr.File(label="上传音频文件", file_types=["audio"])
                ref_image_input = gr.File(label="上传参考图像（可选）", file_types=["image"])
                video_extension_checkbox = gr.Checkbox(label="是否扩展视频", value=False)
                synthesize_btn = gr.Button("合成视频")
            with gr.Column():
                video_output = gr.Video(label="合成的视频")
                status_output = gr.Textbox(label="状态信息", lines=5)

        synthesize_btn.click(
            fn=synthesize_video,
            inputs=[video_input, audio_input, ref_image_input, video_extension_checkbox],
            outputs=[video_output, status_output]
        )


def liveportrait_tab():
    """LivePortrait视频生成Tab"""

    def generate_video(image, audio, template_id, video_fps, mouth_move_strength):
        # 保存上传的文件
        image_path = save_uploaded_file(image)
        audio_path = save_uploaded_file(audio)

        if not image_path or not audio_path:
            return None, "请上传图像和音频文件"

        # 上传文件到临时服务器（模拟）
        image_url = upload_file_to_temp_server(image_path)
        audio_url = upload_file_to_temp_server(audio_path)

        # 调用视频生成函数
        try:
            result_video_url = test_liveportrait(
                DASHSCOPE_API_KEY,
                image_url=image_url,
                audio_url=audio_url,
                template_id=template_id,
                video_fps=video_fps,
                mouth_move_strength=mouth_move_strength
            )

            if result_video_url:
                # 下载生成的视频
                result_path = os.path.join(TEMP_DIR, f"liveportrait_result.mp4")
                response = requests.get(result_video_url)
                with open(result_path, "wb") as f:
                    f.write(response.content)
                return result_path, f"视频生成成功！\n视频URL: {result_video_url}"
            else:
                return None, "视频生成失败"
        except Exception as e:
            return None, f"视频生成过程中出现错误: {str(e)}"

    with gr.Column():
        gr.Markdown("## LivePortrait视频生成")
        with gr.Row():
            with gr.Column():
                image_input = gr.File(label="上传人物图像", file_types=["image"])
                audio_input = gr.File(label="上传音频文件", file_types=["audio"])
                template_dropdown = gr.Dropdown(
                    choices=["normal", "minimal", "extreme"],
                    value="normal",
                    label="模板ID"
                )
                fps_slider = gr.Slider(
                    minimum=20,
                    maximum=60,
                    value=30,
                    step=1,
                    label="视频帧率"
                )
                mouth_strength_slider = gr.Slider(
                    minimum=0.1,
                    maximum=2.0,
                    value=1.0,
                    step=0.1,
                    label="嘴部运动强度"
                )
                generate_btn = gr.Button("生成视频")
            with gr.Column():
                video_output = gr.Video(label="生成的视频")
                status_output = gr.Textbox(label="状态信息", lines=5)

        generate_btn.click(
            fn=generate_video,
            inputs=[image_input, audio_input, template_dropdown, fps_slider, mouth_strength_slider],
            outputs=[video_output, status_output]
        )


def wanx21vaceplus_tab():
    """Wanx2.1-Vace-Plus视频生成Tab"""

    def generate_video(function_option, prompt, ref_images, video_file, mask_image,
                       first_clip, mask_frame_id, control_condition, mask_type,
                       expand_ratio, top_scale, bottom_scale, left_scale, right_scale,
                       obj_or_bg, size):
        # 根据功能选项处理不同的输入
        kwargs = {"prompt": prompt}

        if function_option == "image_reference":
            # 处理参考图像
            ref_image_urls = []
            if ref_images:
                for ref_image in ref_images:
                    ref_image_path = save_uploaded_file(ref_image)
                    if ref_image_path:
                        ref_image_url = upload_file_to_temp_server(ref_image_path)
                        ref_image_urls.append(ref_image_url)
            kwargs["ref_images_url"] = ref_image_urls
            kwargs["obj_or_bg"] = obj_or_bg
            kwargs["size"] = size

        elif function_option == "video_repainting":
            # 处理视频重绘
            if video_file:
                video_path = save_uploaded_file(video_file)
                if video_path:
                    video_url = upload_file_to_temp_server(video_path)
                    kwargs["video_url"] = video_url
            kwargs["control_condition"] = control_condition

        elif function_option == "video_edit":
            # 处理视频编辑
            if video_file:
                video_path = save_uploaded_file(video_file)
                if video_path:
                    video_url = upload_file_to_temp_server(video_path)
                    kwargs["video_url"] = video_url
            if mask_image:
                mask_image_path = save_uploaded_file(mask_image)
                if mask_image_path:
                    mask_image_url = upload_file_to_temp_server(mask_image_path)
                    kwargs["mask_image_url"] = mask_image_url
            kwargs["mask_frame_id"] = mask_frame_id
            kwargs["mask_type"] = mask_type
            kwargs["expand_ratio"] = expand_ratio

        elif function_option == "video_extension":
            # 处理视频扩展
            if first_clip:
                first_clip_path = save_uploaded_file(first_clip)
                if first_clip_path:
                    first_clip_url = upload_file_to_temp_server(first_clip_path)
                    kwargs["first_clip_url"] = first_clip_url

        elif function_option == "video_outpainting":
            # 处理视频外绘
            if video_file:
                video_path = save_uploaded_file(video_file)
                if video_path:
                    video_url = upload_file_to_temp_server(video_path)
                    kwargs["video_url"] = video_url
            kwargs["top_scale"] = top_scale
            kwargs["bottom_scale"] = bottom_scale
            kwargs["left_scale"] = left_scale
            kwargs["right_scale"] = right_scale

        # 调用视频生成函数
        try:
            result_video_url = test_wanx21_vace_plus(
                DASHSCOPE_API_KEY,
                function_option,
                **kwargs
            )

            if result_video_url:
                # 下载生成的视频
                result_path = os.path.join(TEMP_DIR, f"wanx21vaceplus_result.mp4")
                response = requests.get(result_video_url)
                with open(result_path, "wb") as f:
                    f.write(response.content)
                return result_path, f"视频生成成功！\n视频URL: {result_video_url}"
            else:
                return None, "视频生成失败"
        except Exception as e:
            return None, f"视频生成过程中出现错误: {str(e)}"

    with gr.Column():
        gr.Markdown("## Wanx2.1-Vace-Plus视频生成")

        # 功能选项
        function_option = gr.Radio(
            choices=[
                ("图像参考生视频", "image_reference"),
                ("视频重绘", "video_repainting"),
                ("视频编辑", "video_edit"),
                ("视频扩展", "video_extension"),
                ("视频外绘", "video_outpainting")
            ],
            value="image_reference",
            label="选择功能"
        )

        with gr.Row():
            with gr.Column():
                # 通用参数
                prompt_input = gr.Textbox(
                    label="视频描述文本",
                    placeholder="请输入视频描述文本...",
                    lines=3
                )

                # Image Reference 参数
                with gr.Group(visible=True) as image_reference_group:
                    gr.Markdown("### 图像参考参数")
                    ref_images_input = gr.File(
                        label="上传参考图像（可多选）",
                        file_types=["image"],
                        file_count="multiple"
                    )
                    obj_or_bg_checkboxes = gr.CheckboxGroup(
                        choices=["obj", "bg"],
                        value=["obj", "bg"],
                        label="对象或背景处理选项"
                    )
                    size_dropdown = gr.Dropdown(
                        choices=["1280*720", "1920*1080"],
                        value="1280*720",
                        label="视频尺寸"
                    )

                # Video Repainting 参数
                with gr.Group(visible=False) as video_repainting_group:
                    gr.Markdown("### 视频重绘参数")
                    video_repainting_input = gr.File(
                        label="上传原始视频",
                        file_types=["video"]
                    )
                    control_condition_dropdown = gr.Dropdown(
                        choices=["depth", "canny", "hed"],
                        value="depth",
                        label="控制条件"
                    )

                # Video Edit 参数
                with gr.Group(visible=False) as video_edit_group:
                    gr.Markdown("### 视频编辑参数")
                    video_edit_input = gr.File(
                        label="上传原始视频",
                        file_types=["video"]
                    )
                    mask_image_input = gr.File(
                        label="上传遮罩图像",
                        file_types=["image"]
                    )
                    mask_frame_id_number = gr.Number(
                        value=1,
                        label="遮罩帧ID"
                    )
                    mask_type_dropdown = gr.Dropdown(
                        choices=["tracking", "static"],
                        value="tracking",
                        label="遮罩类型"
                    )
                    expand_ratio_slider = gr.Slider(
                        minimum=0.01,
                        maximum=0.5,
                        value=0.05,
                        step=0.01,
                        label="扩展比例"
                    )

                # Video Extension 参数
                with gr.Group(visible=False) as video_extension_group:
                    gr.Markdown("### 视频扩展参数")
                    first_clip_input = gr.File(
                        label="上传第一个视频片段",
                        file_types=["video"]
                    )

                # Video Outpainting 参数
                with gr.Group(visible=False) as video_outpainting_group:
                    gr.Markdown("### 视频外绘参数")
                    video_outpainting_input = gr.File(
                        label="上传原始视频",
                        file_types=["video"]
                    )
                    with gr.Row():
                        top_scale_slider = gr.Slider(
                            minimum=1.0,
                            maximum=3.0,
                            value=1.5,
                            step=0.1,
                            label="顶部扩展比例"
                        )
                        bottom_scale_slider = gr.Slider(
                            minimum=1.0,
                            maximum=3.0,
                            value=1.5,
                            step=0.1,
                            label="底部扩展比例"
                        )
                    with gr.Row():
                        left_scale_slider = gr.Slider(
                            minimum=1.0,
                            maximum=3.0,
                            value=1.5,
                            step=0.1,
                            label="左侧扩展比例"
                        )
                        right_scale_slider = gr.Slider(
                            minimum=1.0,
                            maximum=3.0,
                            value=1.5,
                            step=0.1,
                            label="右侧扩展比例"
                        )

                generate_btn = gr.Button("生成视频")

            with gr.Column():
                video_output = gr.Video(label="生成的视频")
                status_output = gr.Textbox(label="状态信息", lines=10)

        # 功能选项变化时显示/隐藏对应参数组
        def update_visibility(selected_option):
            visibility_map = {
                "image_reference": [gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                                    gr.update(visible=False), gr.update(visible=False)],
                "video_repainting": [gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                                     gr.update(visible=False), gr.update(visible=False)],
                "video_edit": [gr.update(visible=False), gr.update(visible=False), gr.update(visible=True),
                               gr.update(visible=False), gr.update(visible=False)],
                "video_extension": [gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                                    gr.update(visible=True), gr.update(visible=False)],
                "video_outpainting": [gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                                      gr.update(visible=False), gr.update(visible=True)]
            }
            return visibility_map.get(selected_option, [gr.update(visible=False)] * 5)

        function_option.change(
            fn=update_visibility,
            inputs=function_option,
            outputs=[
                image_reference_group,
                video_repainting_group,
                video_edit_group,
                video_extension_group,
                video_outpainting_group
            ]
        )

        generate_btn.click(
            fn=generate_video,
            inputs=[
                function_option, prompt_input, ref_images_input, video_repainting_input, mask_image_input,
                first_clip_input, mask_frame_id_number, control_condition_dropdown, mask_type_dropdown,
                expand_ratio_slider, top_scale_slider, bottom_scale_slider, left_scale_slider, right_scale_slider,
                obj_or_bg_checkboxes, size_dropdown
            ],
            outputs=[video_output, status_output]
        )


# 创建Gradio界面
with gr.Blocks(title="视频生成演示平台") as demo:
    gr.Markdown("# 视频生成演示平台")
    gr.Markdown("支持多种AI视频生成模型，通过Tab选择不同的功能模块")

    with gr.Tabs():
        with gr.TabItem("万象数字人"):
            wan22s2v_tab()

        with gr.TabItem("VideoRetalk"):
            videoretalk_tab()

        with gr.TabItem("LivePortrait"):
            liveportrait_tab()

        with gr.TabItem("Wanx2.1-Vace-Plus"):
            wanx21vaceplus_tab()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Minimal test wrapper for batch_wan26_edit.run_batch.

Steps:
  1) export DASHSCOPE_API_KEY='sk-xxx'
  2) python3 test_smoke.py

It writes a tiny jobs.smoke.jsonl (one job) and runs run_batch() once.
"""

from pathlib import Path

import batch_wan26_edit as wan


def test_run_one_job() -> None:
    here = Path(__file__).parent
    jobs_path = here / "jobs.smoke.jsonl"
    out_dir = here / "out_smoke"

    # One job, uses your local reference photo (auto base64-encoded by the library).
    jobs_path.write_text(
        "\n".join(
            [
                "{"
                '"id":"smoke",'
                '"prompt":"以参考图为主体特征，生成竖屏电影级写实篮球人物图，强对比光影，暗金色调，背景简洁，画面不要任何文字、数字、logo、水印",'
                '"images":["/Users/test/Downloads/tumblr_inline_mn7ypkwCbr1qz4rgp.jpg"],'
                '"size":"720*1280",'
                '"n":1,'
                '"negative_prompt":"文字, 字幕, logo, 品牌标识, 水印, 数字, 球衣号码"'
                "}"
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print("[test] jobs:", jobs_path)
    print("[test] out:", out_dir)

    jobs, images = wan.run_batch(
        in_path=jobs_path,
        out_dir=out_dir,
        default_size="720*1280",
        default_n=1,
        watermark=False,
        prompt_extend=True,
        sleep_s=0.0,
    )

    print(f"[test] done: jobs={jobs}, images_saved={images}")


if __name__ == "__main__":
    test_run_one_job()

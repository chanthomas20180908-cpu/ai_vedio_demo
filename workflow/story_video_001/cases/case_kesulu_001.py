from __future__ import annotations

from workflow.story_video_001.activities.activity_script_001 import main
from workflow.story_video_001.profiles.profile_kesulu_001 import PROFILE

'''
PYTHONPATH=/Users/test/code/Python/AI_vedio_demo/pythonProject \
/Users/test/code/Python/AI_vedio_demo/pythonProject/.venv/bin/python3 \
  -m workflow.story_video_001.cases.case_kesulu_001 \
  --input '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/my_mutimedia/my_scripts/唐僧克苏鲁/塞勒菲斯/03_split_md_20260311_113158/001_整篇__seg003.md'
'''

if __name__ == "__main__":
    raise SystemExit(main(profile=PROFILE))

## 任务
新增生成图片的方式,并修改在工作流中[activity_script_001.py](../workflow/story_video_001/activities/activity_script_001.py)的调用改为新的生图方式
## 参考
### 生图调用
from openai import OpenAI

client = OpenAI(
    base_url='https://api.cloubic.com/v1',
    api_key='CLOUBIC_API_KEY'
)

response = client.chat.completions.create(
    model="gemini-3.1-flash-image-preview",
    messages=[
        {
            "role": "user",
            "content": "生成一只可爱的小猫在草地上玩耍的图片"
        }
    ]
)

print(response.choices[0].message.content)
## 要求
先给我修改方案,不要着急修改执行
CosyVoice声音复刻服务基于生成式语音大模型，使用10~20秒音频样本即可生成高度相似且自然的定制声音，无需传统训练过程。声音复刻与语音合成是前后关联的两个步骤。本文档聚焦于介绍声音复刻的参数和接口细节，语音合成请参见[实时语音合成-CosyVoice/Sambert](https://help.aliyun.com/zh/model-studio/text-to-speech)。

**用户指南：**关于模型介绍和选型建议请参见[实时语音合成-CosyVoice/Sambert](https://help.aliyun.com/zh/model-studio/text-to-speech)。

## **音频要求**

高质量的输入音频是获得优质复刻效果的基础。

| **项目** | **要求** |
| --- | --- |
| **支持格式** | WAV (16bit), MP3, M4A |
| **音频时长** | 推荐10~20秒，最长不得超过60秒 |
| **文件大小** | ≤ 10 MB |
| **采样率** | ≥ 16 kHz |
| **声道** | 单声道 / 双声道，双声道音频仅处理首声道，请确保首声道包含有效人声 |
| **内容** | 音频必须包含至少5秒连续清晰朗读（无背景音），其余部分仅允许短暂停顿（≤2秒）；整段音频应避免背景音乐、噪音或其他人声，确保核心朗读内容质量；请使用正常说话音频作为输入，不要上传歌曲或唱歌音频，以确保复刻效果准确和可用。 |
| **语言** | 因驱动音色的语音合成模型（通过`target_model`/`targetModel`参数指定）而异： - cosyvoice-v1、cosyvoice-v2：中文（普通话）、英文 - cosyvoice-v3-flash、cosyvoice-v3-plus：中文（普通话、广东话、东北话、甘肃话、贵州话、河南话、湖北话、江西话、闽南话、宁夏话、山西话、陕西话、山东话、上海话、四川话、天津话、云南话）、英文、法语、德语、日语、韩语、俄语 |

## 快速开始：从复刻到合成

![image](https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/9087717671/CAEQYxiBgMCNsMj91BkiIDdiMWQyMmQ0MzMzNjRjNGU4OGViYTU2MTE1OTExNTg05899512_20251120114927.389.svg)

### 1\. 工作流程

声音复刻与语音合成是紧密关联的两个独立步骤，遵循“先创建，后使用”的流程：

1.  创建音色
    
    调用[创建音色](#1eaa57d82did9)接口，上传一段音频。系统会分析该音频，创建一个专属的复刻音色。**此步骤必须指定**`**target_model**`**/**`**targetModel**`**，声明创建的音色将由哪个语音合成模型驱动。**
    
    若已有创建好的音色（调用[查询音色列表](#401d33226330i)接口查看），可跳过这一步直接进行下一步。
    
2.  使用音色进行语音合成
    
    调用语音合成接口，传入上一步获得的音色。**此步骤指定的语音合成模型必须和上一步的**`**target_model**`**/**`**targetModel**`**一致。**
    

### 2\. 模型配置与准备工作

选择合适的模型并完成准备工作。

#### 模型配置

声音复刻时需要指定以下两个模型：

-   声音复刻模型：voice-enrollment
    
-   驱动音色的语音合成模型：
    
    在资源与预算允许的情况下，推荐使用`cosyvoice-v3-plus`以获得最佳效果。
    
    | **版本** | **适用场景** |
    | --- | --- |
    | **cosyvoice-v3-plus** | 追求最佳音质与表现力，预算充足 |
    | **cosyvoice-v3-flash** | 平衡效果与成本，综合性价比高 |
    | **cosyvoice-v2** | 兼容旧版或低要求场景 |
    | **cosyvoice-v1** | 兼容旧版或低要求场景 |
    

#### 准备工作

1.  **获取API Key**：[获取与配置 API Key](https://help.aliyun.com/zh/model-studio/get-api-key)，为安全起见，推荐将API Key配置到环境变量。
    
2.  **安装SDK**：确保已[安装最新版DashScope SDK](https://help.aliyun.com/zh/model-studio/install-sdk)。
    
3.  **准备音频URL**：将符合[音频要求](#音频要求与最佳实践)的音频文件上传至公网可访问的位置，如[阿里云对象存储OSS](https://help.aliyun.com/zh/oss/user-guide/simple-upload#a632b50f190j8)，并确保URL可公开访问。
    

### 3\. 端到端示例：从复刻到合成

以下示例演示了如何在语音合成中使用声音复刻生成的专属音色，实现与原音高度相似的输出效果。

-   **关键原则**：声音复刻时，`target_model`（驱动音色的语音合成模型）必须与后续调用语音合成接口时指定的语音合成模型一致，否则会合成失败。
    
-   注意将示例中的`AUDIO_URL`替换为实际的音频URL。
    

```
import os
import time
import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer

# 1. 环境准备
# 推荐通过环境变量配置API Key
# export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
if not dashscope.api_key:
    raise ValueError("DASHSCOPE_API_KEY environment variable not set.")

# 2. 定义复刻参数
TARGET_MODEL = "cosyvoice-v3-plus" 
# 为音色起一个有意义的前缀
VOICE_PREFIX = "myvoice" # 仅允许数字和小写字母，小于十个字符
# 公网可访问音频URL
AUDIO_URL = "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/cosyvoice/cosyvoice-zeroshot-sample.wav" # 示例URL，请替换为自己的

# 3. 创建音色 (异步任务)
print("--- Step 1: Creating voice enrollment ---")
service = VoiceEnrollmentService()
try:
    voice_id = service.create_voice(
        target_model=TARGET_MODEL,
        prefix=VOICE_PREFIX,
        url=AUDIO_URL
    )
    print(f"Voice enrollment submitted successfully. Request ID: {service.get_last_request_id()}")
    print(f"Generated Voice ID: {voice_id}")
except Exception as e:
    print(f"Error during voice creation: {e}")
    raise e
# 4. 轮询查询音色状态
print("\n--- Step 2: Polling for voice status ---")
max_attempts = 30
poll_interval = 10 # 秒
for attempt in range(max_attempts):
    try:
        voice_info = service.query_voice(voice_id=voice_id)
        status = voice_info.get("status")
        print(f"Attempt {attempt + 1}/{max_attempts}: Voice status is '{status}'")
        
        if status == "OK":
            print("Voice is ready for synthesis.")
            break
        elif status == "UNDEPLOYED":
            print(f"Voice processing failed with status: {status}. Please check audio quality or contact support.")
            raise RuntimeError(f"Voice processing failed with status: {status}")
        # 对于 "DEPLOYING" 等中间状态，继续等待
        time.sleep(poll_interval)
    except Exception as e:
        print(f"Error during status polling: {e}")
        time.sleep(poll_interval)
else:
    print("Polling timed out. The voice is not ready after several attempts.")
    raise RuntimeError("Polling timed out. The voice is not ready after several attempts.")

# 5. 使用复刻音色进行语音合成
print("\n--- Step 3: Synthesizing speech with the new voice ---")
try:
    synthesizer = SpeechSynthesizer(model=TARGET_MODEL, voice=voice_id)
    text_to_synthesize = "恭喜，已成功复刻并合成了属于自己的声音！"
    
    # call()方法返回二进制音频数据
    audio_data = synthesizer.call(text_to_synthesize)
    print(f"Speech synthesis successful. Request ID: {synthesizer.get_last_request_id()}")

    # 6. 保存音频文件
    output_file = "my_custom_voice_output.mp3"
    with open(output_file, "wb") as f:
        f.write(audio_data)
    print(f"Audio saved to {output_file}")

except Exception as e:
    print(f"Error during speech synthesis: {e}")
```

## **API参考**

使用不同 API 时，请确保使用同一账号进行操作。

### **创建音色**

上传用于复刻的音频，创建自定义音色。

## Python SDK

#### **接口说明**

```
def create_voice(self, target_model: str, prefix: str, url: str, language_hints: List[str] = None) -> str:
    '''
    创建一个新的定制音色。
    param: target_model 驱动音色的语音合成模型，必须与后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败。推荐 cosyvoice-v3-flash 或 cosyvoice-v3-plus。
    param: prefix 为音色指定一个便于识别的名称（仅允许数字、大小写字母和下划线，不超过10个字符）。建议选用与角色、场景相关的标识。该关键字会在复刻的音色名中出现，生成的音色名格式为：模型名-前缀-唯一标识，如cosyvoice-v3-plus-myvoice-xxxxxxxx。
    param: url 用于复刻音色的音频文件URL，要求公网可访问。
    param: language_hints 指定用于提取目标音色特征的样本音频语种，仅适用于 cosyvoice-v3-flash 和 cosyvoice-v3-plus 模型。
            该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。
            若设置的语言提示与实际音频语言不符（例如为中文音频设置 en），系统将忽略此提示，并依据音频内容自动检测语言。
            取值范围：zh（默认值）、en、fr、de、ja、ko、ru。此参数为数组，但当前版本仅处理第一个元素，建议只传入一个值。
    return: voice_id 音色ID，可直接用于语音合成接口的voice参数。
    '''
```

**重要**

-   `target_model`：驱动音色的语音合成模型，须和后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败
    
-   `language_hints`：指定用于提取目标音色特征的样本音频语种，仅适用于cosyvoice-v3-flash和cosyvoice-v3-plus模型
    
    功能说明：该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。若设置的语言提示与实际音频语言不符（例如为中文音频设置 `en`），系统将忽略此提示，并依据音频内容自动检测语言。
    
    取值范围：
    
    -   zh：中文（默认值）
        
    -   en：英文
        
    -   fr：法语
        
    -   de：德语
        
    -   ja：日语
        
    -   ko：韩语
        
    -   ru：俄语
        
    
    **注意**：此参数为数组，但当前版本仅处理第一个元素，因此建议只传入一个值。
    

#### **请求示例**

```
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()

# 避免频繁调用。每次调用都会创建新音色，达到配额上限后将无法创建。
voice_id = service.create_voice(
    target_model='cosyvoice-v3-plus',
    prefix='myvoice',
    url='https://your-audio-file-url',
    language_hints=['zh']
)

print(f"Request ID: {service.get_last_request_id()}")
print(f"Voice ID: {voice_id}")
```

## Java SDK

#### **接口说明**

```
/**
 * 创建一个新的定制音色。
 *
 * @param targetModel 驱动音色的语音合成模型，必须与后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败。推荐 cosyvoice-v3-flash 或 cosyvoice-v3-plus。
 * @param prefix 为音色指定一个便于识别的名称（仅允许数字、大小写字母和下划线，不超过10个字符）。建议选用与角色、场景相关的标识。该关键字会在复刻的音色名中出现，生成的音色名格式为：模型名-前缀-唯一标识，如cosyvoice-v3-plus-myvoice-xxxxxxxx。
 * @param url 用于复刻音色的音频文件URL，要求公网可访问。
 * @param customParam 自定义参数。可在此处指定languageHints。
 *                  languageHints指定用于提取目标音色特征的样本音频语种，仅适用于 cosyvoice-v3-flash 和 cosyvoice-v3-plus 模型。
 *                  该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。
 *                  若设置的语言提示与实际音频语言不符（例如为中文音频设置 en），系统将忽略此提示，并依据音频内容自动检测语言。
 *                  取值范围：zh（默认值）、en、fr、de、ja、ko、ru。此参数为数组，但当前版本仅处理第一个元素，建议只传入一个值。
 * @return Voice 新创建的音色，通过Voice的getVoiceId方法能够获取音色ID，可直接用于语音合成接口的voice参数。
 * @throws NoApiKeyException 如果apikey为空。
 * @throws InputRequiredException 如果必须参数为空。
 */
public Voice createVoice(String targetModel, String prefix, String url, VoiceEnrollmentParam customParam) throws NoApiKeyException, InputRequiredException
```

**重要**

-   `targetModel`：驱动音色的语音合成模型，须和后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败
    
-   `languageHints`：指定用于提取目标音色特征的样本音频语种，仅适用于cosyvoice-v3-flash和cosyvoice-v3-plus模型
    
    功能说明：该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。若设置的语言提示与实际音频语言不符（例如为中文音频设置 `en`），系统将忽略此提示，并依据音频内容自动检测语言。
    
    取值范围：
    
    -   zh：中文（默认值）
        
    -   en：英文
        
    -   fr：法语
        
    -   de：德语
        
    -   ja：日语
        
    -   ko：韩语
        
    -   ru：俄语
        
    
    **注意**：此参数为数组，但当前版本仅处理第一个元素，因此建议只传入一个值。
    

#### **请求示例**

```
import com.alibaba.dashscope.audio.ttsv2.enrollment.Voice;
import com.alibaba.dashscope.audio.ttsv2.enrollment.VoiceEnrollmentParam;
import com.alibaba.dashscope.audio.ttsv2.enrollment.VoiceEnrollmentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collections;

public class Main {
    private static final Logger logger = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args) {
        String apiKey = System.getenv("DASHSCOPE_API_KEY");
        String targetModel = "cosyvoice-v3-plus";
        String prefix = "myvoice";
        String fileUrl = "https://your-audio-file-url";
        String cloneModelName = "voice-enrollment";

        try {
            VoiceEnrollmentService service = new VoiceEnrollmentService(apiKey);
            Voice myVoice = service.createVoice(
                    targetModel,
                    prefix,
                    fileUrl,
                    VoiceEnrollmentParam.builder()
                    .model(cloneModelName)
                    .languageHints(Collections.singletonList("zh")).build());

            logger.info("Voice creation submitted. Request ID: {}", service.getLastRequestId());
            logger.info("Generated Voice ID: {}", myVoice.getVoiceId());
        } catch (Exception e) {
            logger.error("Failed to create voice", e);
        }
    }
}
```

## RESTful API

#### **基本信息**

| URL | ``` https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization ``` |
| --- | --- |
| 请求方法 | POST |
| 请求头 | ``` Authorization: Bearer {api-key} // 需替换为您自己的API Key Content-Type: application/json ``` |
| 消息体 | 包含所有请求参数的消息体如下，对于可选字段，在实际业务中可根据需求省略： **重要** - `model`：声音复刻模型，固定为`voice-enrollment` - `target_model`：驱动音色的语音合成模型，须和后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败 - `language_hints`：指定用于提取目标音色特征的样本音频语种，仅适用于cosyvoice-v3-flash和cosyvoice-v3-plus模型 功能说明：该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。若设置的语言提示与实际音频语言不符（例如为中文音频设置 `en`），系统将忽略此提示，并依据音频内容自动检测语言。 取值范围： - zh：中文（默认值） - en：英文 - fr：法语 - de：德语 - ja：日语 - ko：韩语 - ru：俄语 **注意**：此参数为数组，但当前版本仅处理第一个元素，因此建议只传入一个值。 ``` { "model": "voice-enrollment", "input": { "action": "create_voice", "target_model": "cosyvoice-v3-plus", "prefix": "myvoice", "url": "https://yourAudioFileUrl", "language_hints": ["zh"] } } ``` |

#### **请求参数**

**点击查看请求示例**

**重要**

-   `model`：声音复刻模型，固定为`voice-enrollment`
    
-   `target_model`：驱动音色的语音合成模型，须和后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败
    
-   `language_hints`：指定用于提取目标音色特征的样本音频语种，仅适用于cosyvoice-v3-flash和cosyvoice-v3-plus模型
    
    功能说明：该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。若设置的语言提示与实际音频语言不符（例如为中文音频设置 `en`），系统将忽略此提示，并依据音频内容自动检测语言。
    
    取值范围：
    
    -   zh：中文（默认值）
        
    -   en：英文
        
    -   fr：法语
        
    -   de：德语
        
    -   ja：日语
        
    -   ko：韩语
        
    -   ru：俄语
        
    
    **注意**：此参数为数组，但当前版本仅处理第一个元素，因此建议只传入一个值。
    

```
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H "Content-Type: application/json" \
-d '{
    "model": "voice-enrollment",
    "input": {
        "action": "create_voice",
        "target_model": "cosyvoice-v3-plus",
        "prefix": "myvoice",
        "url": "https://yourAudioFileUrl",
        "language_hints": ["zh"]
    }
}'
```

| **参数** | **类型** | **默认值** | **是否必须** | **说明** |
| --- | --- | --- | --- | --- |
| model | string | \\- | 是   | 声音复刻模型，固定为`voice-enrollment`。 |
| action | string | \\- | 是   | 操作类型，固定为`create_voice`。 |
| target\\_model | string | \\- | 是   | 驱动音色的语音合成模型，推荐 cosyvoice-v3-flash 或 cosyvoice-v3-plus。 必须与后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败。 |
| prefix | string | \\- | 是   | 为音色指定一个便于识别的名称（仅允许数字、大小写字母和下划线，不超过10个字符）。建议选用与角色、场景相关的标识。 > 该关键字会在复刻的音色名中出现，生成的音色名格式为：`模型名-前缀-唯一标识`，如`cosyvoice-v3-plus-myvoice-xxxxxxxx`。 |
| url | string | \\- | 是   | 用于复刻音色的音频文件URL，要求公网可访问。 |
| language\\_hints | array\\[string\\] | \\["zh"\\] | 否   | 指定用于提取目标音色特征的样本音频语种，仅适用于 cosyvoice-v3-flash 和 cosyvoice-v3-plus 模型。 功能说明：该参数用于辅助模型识别样本音频（原始参考音频）的语种，从而更准确地提取音色特征，提升复刻效果。若设置的语言提示与实际音频语言不符（例如为中文音频设置 `en`），系统将忽略此提示，并依据音频内容自动检测语言。 取值范围： - zh：中文（默认值） - en：英文 - fr：法语 - de：德语 - ja：日语 - ko：韩语 - ru：俄语 **注意**：此参数为数组，但当前版本仅处理第一个元素，因此建议只传入一个值。 |

#### **响应参数**

**点击查看响应示例**

```
{
    "output": {
        "voice_id": "yourVoiceId"
    },
    "usage": {
        "count": 1
    },
    "request_id": "yourRequestId"
}
```

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| voice\\_id | string | 音色ID，可直接用于语音合成接口的`voice`参数。 |

### **查询音色列表**

分页查询已创建的音色列表。

## Python SDK

#### **接口说明**

```
def list_voices(self, prefix=None, page_index: int = 0, page_size: int = 10) -> List[dict]:
    '''
    查询已创建的所有音色
    param: prefix 音色自定义前缀，仅允许数字和小写字母，长度小于10个字符。
    param: page_index 查询的页索引
    param: page_size 查询页大小
    return: List[dict] 音色列表，包含每个音色的id，创建时间，修改时间，状态。格式为：[{'gmt_create': '2025-10-09 14:51:01', 'gmt_modified': '2025-10-09 14:51:07', 'status': 'OK', 'voice_id': 'cosyvoice-v3-myvoice-xxx'}]
    音色状态有三种：
        DEPLOYING： 审核中
        OK：审核通过，可调用
        UNDEPLOYED：审核不通过，不可调用
    '''
```

#### **请求示例**

```
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()

# 按前缀筛选，或设为None查询所有
voices = service.list_voices(prefix='myvoice', page_index=0, page_size=10)

print(f"Request ID: {service.get_last_request_id()}")
print(f"Found voices: {voices}")
```

#### **响应示例**

```
[
    {
        "gmt_create": "2024-09-13 11:29:41",
        "voice_id": "yourVoiceId",
        "gmt_modified": "2024-09-13 11:29:41",
        "status": "OK"
    },
    {
        "gmt_create": "2024-09-13 13:22:38",
        "voice_id": "yourVoiceId",
        "gmt_modified": "2024-09-13 13:22:38",
        "status": "OK"
    }
]
```

#### **响应参数**

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| voice\\_id | string | 音色ID。 |
| gmt\\_create | string | 创建音色的时间。 |
| gmt\\_modified | string | 修改音色的时间。 |
| status | string | 音色状态： - DEPLOYING： 审核中 - OK：审核通过，可调用 - UNDEPLOYED：审核不通过，不可调用 |

## Java SDK

#### **接口说明**

```
// 音色状态有三种：
//        DEPLOYING： 审核中
//        OK：审核通过，可调用
//        UNDEPLOYED：审核不通过，不可调用
/**
 * 查询已创建的所有音色 默认的页索引为0，默认的页大小为10
 *
 * @param prefix 音色自定义前缀，仅允许数字和小写字母，长度小于10个字符。可以为null。
 * @return Voice[] 音色对象数组。Voice封装了音色的id，创建时间，修改时间，状态。
 * @throws NoApiKeyException 如果apikey为空。
 * @throws InputRequiredException 如果必须参数为空。
 */
public Voice[] listVoice(String prefix) throws NoApiKeyException, InputRequiredException 

/**
 * 查询已创建的所有音色
 *
 * @param prefix 音色自定义前缀，仅允许数字和小写字母，长度小于10个字符。
 * @param pageIndex 查询的页索引。
 * @param pageSize 查询的页大小。
 * @return Voice[] 音色对象数组。Voice封装了音色的id，创建时间，修改时间，状态。
 * @throws NoApiKeyException 如果apikey为空。
 * @throws InputRequiredException 如果必须参数为空。
 */
public Voice[] listVoice(String prefix, int pageIndex, int pageSize) throws NoApiKeyException, InputRequiredException
```

#### **请求示例**

需要引入第三方库`com.google.gson.Gson`。

```
import com.alibaba.dashscope.audio.ttsv2.enrollment.Voice;
import com.alibaba.dashscope.audio.ttsv2.enrollment.VoiceEnrollmentService;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.google.gson.Gson;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Main {
    public static String apiKey = System.getenv("DASHSCOPE_API_KEY");  // 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
    private static String prefix = "myvoice"; // 请按实际情况进行替换
    private static final Logger logger = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args)
            throws NoApiKeyException, InputRequiredException {
        VoiceEnrollmentService service = new VoiceEnrollmentService(apiKey);
        // 查询音色
        Voice[] voices = service.listVoice(prefix, 0, 10);
        logger.info("List successful. Request ID: {}", service.getLastRequestId());
        logger.info("Voices Details: {}", new Gson().toJson(voices));
    }
}
```

### **响应示例**

```
[
    {
        "gmt_create": "2024-09-13 11:29:41",
        "voice_id": "yourVoiceId",
        "gmt_modified": "2024-09-13 11:29:41",
        "status": "OK"
    },
    {
        "gmt_create": "2024-09-13 13:22:38",
        "voice_id": "yourVoiceId",
        "gmt_modified": "2024-09-13 13:22:38",
        "status": "OK"
    }
]
```

### **响应参数**

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| voice\\_id | string | 音色ID。 |
| gmt\\_create | string | 创建音色的时间。 |
| gmt\\_modified | string | 修改音色的时间。 |
| status | string | 音色状态： - DEPLOYING： 审核中 - OK：审核通过，可调用 - UNDEPLOYED：审核不通过，不可调用 |

## RESTful API

#### **基本信息**

| URL | ``` https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization ``` |
| --- | --- |
| 请求方法 | POST |
| 请求头 | ``` Authorization: Bearer {api-key} // 需替换为您自己的API Key Content-Type: application/json ``` |
| 消息体 | 包含所有请求参数的消息体如下，对于可选字段，在实际业务中可根据需求省略： **重要** `model`为声音复刻模型，固定为`voice-enrollment`。 ``` { "model": "voice-enrollment", "input": { "action": "list_voice", "prefix": "myvoice", "page_index": 0, "page_size": 10 } } ``` |

#### **请求参数**

**点击查看请求示例**

**重要**

`model`为声音复刻模型，固定为`voice-enrollment`。

```
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H "Content-Type: application/json" \
-d '{
    "model": "voice-enrollment",
    "input": {
        "action": "list_voice",
        "prefix": "myvoice",
        "page_index": 0,
        "page_size": 10
    }
}'
```

| **参数** | **类型** | **默认值** | **是否必须** | **说明** |
| --- | --- | --- | --- | --- |
| model | string | \\- | 是   | 声音复刻模型，固定为`voice-enrollment`。 |
| action | string | \\- | 是   | 操作类型，固定为`list_voice`。 |
| prefix | string | null | 否   | 音色自定义前缀，仅允许数字和小写字母，长度小于10个字符。 |
| page\\_index | integer | 0   | 否   | 页码索引，从0开始计数。 |
| page\\_size | integer | 10  | 否   | 每页包含数据条数。 |

#### **响应参数**

**点击查看响应示例**

```
{
    "output": {
        "voice_list": [
            {
                "gmt_create": "2024-12-11 13:38:02",
                "voice_id": "yourVoiceId",
                "gmt_modified": "2024-12-11 13:38:02",
                "status": "OK"
            }
        ]
    },
    "usage": {
        "count": 1
    },
    "request_id": "yourRequestId"
}
```

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| voice\\_id | string | 音色ID。 |
| gmt\\_create | string | 创建音色的时间。 |
| gmt\\_modified | string | 修改音色的时间。 |
| status | string | 音色状态： - DEPLOYING： 审核中 - OK：审核通过，可调用 - UNDEPLOYED：审核不通过，不可调用 |

### **查询指定音色**

获取特定音色的详细信息

## Python SDK

#### **接口说明**

```
def query_voice(self, voice_id: str) -> List[str]:
    '''
    查询指定音色的详细信息
    param: voice_id 需要查询的音色ID
    return: List[str] 音色详细信息，包含状态、创建时间、音频链接等
    '''
```

#### **请求示例**

```
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
voice_id = 'cosyvoice-v3-plus-myvoice-xxxxxxxx'

voice_details = service.query_voice(voice_id=voice_id)

print(f"Request ID: {service.get_last_request_id()}")
print(f"Voice Details: {voice_details}")
```

#### **响应示例**

```
{
    "gmt_create": "2024-09-13 11:29:41",
    "resource_link": "https://yourAudioFileUrl",
    "target_model": "cosyvoice-v3-plus",
    "gmt_modified": "2024-09-13 11:29:41",
    "status": "OK"
}
```

#### **响应参数**

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| resource\\_link | string | 被复刻的音频的URL。 |
| target\\_model | string | 驱动音色的语音合成模型，推荐 cosyvoice-v3-flash 或 cosyvoice-v3-plus。 必须与后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败。 |
| gmt\\_create | string | 创建音色的时间。 |
| gmt\\_modified | string | 修改音色的时间。 |
| status | string | 音色状态： - DEPLOYING： 审核中 - OK：审核通过，可调用 - UNDEPLOYED：审核不通过，不可调用 |

## Java SDK

#### **接口说明**

```
/**
 * 查询指定音色的详细信息
 *
 * @param voiceId 需要查询的音色ID
 * @return Voice 音色详细信息，包含状态、创建时间、音频链接等
 * @throws NoApiKeyException 如果apikey为空
 * @throws InputRequiredException 如果必须参数为空
 */
public Voice queryVoice(String voiceId) throws NoApiKeyException, InputRequiredException
```

#### **请求示例**

需要引入第三方库`com.google.gson.Gson`。

```
import com.alibaba.dashscope.audio.ttsv2.enrollment.Voice;
import com.alibaba.dashscope.audio.ttsv2.enrollment.VoiceEnrollmentService;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import com.google.gson.Gson;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Main {
    public static String apiKey = System.getenv("DASHSCOPE_API_KEY");  // 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
    private static String voiceId = "cosyvoice-v3-plus-myvoice-xxx"; // 请按实际情况进行替换
    private static final Logger logger = LoggerFactory.getLogger(Main.class);

    public static void main(String[] args)
            throws NoApiKeyException, InputRequiredException {
        VoiceEnrollmentService service = new VoiceEnrollmentService(apiKey);
        Voice voice = service.queryVoice(voiceId);
        
        logger.info("Query successful. Request ID: {}", service.getLastRequestId());
        logger.info("Voice Details: {}", new Gson().toJson(voice));
    }
}
```

### **响应示例**

```
{
    "gmt_create": "2024-09-13 11:29:41",
    "resource_link": "https://yourAudioFileUrl",
    "target_model": "cosyvoice-v3-plus",
    "gmt_modified": "2024-09-13 11:29:41",
    "status": "OK"
}
```

### **响应参数**

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| resource\\_link | string | 被复刻的音频的URL。 |
| target\\_model | string | 驱动音色的语音合成模型，推荐 cosyvoice-v3-flash 或 cosyvoice-v3-plus。 必须与后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败。 |
| gmt\\_create | string | 创建音色的时间。 |
| gmt\\_modified | string | 修改音色的时间。 |
| status | string | 音色状态： - DEPLOYING： 审核中 - OK：审核通过，可调用 - UNDEPLOYED：审核不通过，不可调用 |

## RESTful API

#### **基本信息**

| URL | ``` https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization ``` |
| --- | --- |
| 请求方法 | POST |
| 请求头 | ``` Authorization: Bearer {api-key} // 需替换为您自己的API Key Content-Type: application/json ``` |
| 消息体 | 包含所有请求参数的消息体如下，对于可选字段，在实际业务中可根据需求省略： **重要** `model`为声音复刻模型，固定为`voice-enrollment`。 ``` { "model": "voice-enrollment", "input": { "action": "query_voice", "voice_id": "yourVoiceId" } } ``` |

#### **请求参数**

**点击查看请求示例**

**重要**

`model`为声音复刻模型，固定为`voice-enrollment`。

```
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H "Content-Type: application/json" \
-d '{
    "model": "voice-enrollment",
    "input": {
        "action": "query_voice",
        "voice_id": "yourVoiceId"
    }
}'
```

| **参数** | **类型** | **默认值** | **是否必须** | **说明** |
| --- | --- | --- | --- | --- |
| model | string | \\- | 是   | 声音复刻模型，固定为`voice-enrollment`。 |
| action | string | \\- | 是   | 操作类型，固定为`query_voice`。 |
| voice\\_id | string | \\- | 是   | 需要查询的音色ID。 |

#### **响应参数**

**点击查看响应示例**

```
{
    "output": {
        "gmt_create": "2024-12-11 13:38:02",
        "resource_link": "https://yourAudioFileUrl",
        "target_model": "cosyvoice-v3-plus",
        "gmt_modified": "2024-12-11 13:38:02",
        "status": "OK"
    },
    "usage": {
        "count": 1
    },
    "request_id": "2450f969-d9ea-9483-bafc-************"
}
```

| **参数** | **类型** | **说明** |
| --- | --- | --- |
| resource\\_link | string | 被复刻的音频的URL。 |
| target\\_model | string | 驱动音色的语音合成模型，推荐 cosyvoice-v3-flash 或 cosyvoice-v3-plus。 必须与后续调用语音合成接口时使用的语音合成模型一致，否则合成会失败。 |
| gmt\\_create | string | 创建音色的时间。 |
| gmt\\_modified | string | 修改音色的时间。 |
| status | string | 音色状态： - DEPLOYING： 审核中 - OK：审核通过，可调用 - UNDEPLOYED：审核不通过，不可调用 |

### **更新音色**

使用新的音频文件更新一个已存在的音色。

## Python SDK

#### **接口说明**

```
def update_voice(self, voice_id: str, url: str) -> None:
    '''
    更新音色
    param: voice_id 音色id
    param: url 用于声音复刻的音频文件url
    '''
```

#### **请求示例**

```
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
service.update_voice(
    voice_id='cosyvoice-v3-plus-myvoice-xxxxxxxx',
    url='https://your-new-audio-file-url'
)
print(f"Update submitted. Request ID: {service.get_last_request_id()}")
```

## Java SDK

#### **接口说明**

```
/**
 * 更新音色
 *
 * @param voiceId 需要更新的音色
 * @param url 用于声音复刻的音频文件url
 * @throws NoApiKeyException 如果apikey为空
 * @throws InputRequiredException 如果必须参数为空
 */
public void updateVoice(String voiceId, String url)
    throws NoApiKeyException, InputRequiredException
```

#### **请求示例**

```
import com.alibaba.dashscope.audio.ttsv2.enrollment.VoiceEnrollmentService;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Main {
    public static String apiKey = System.getenv("DASHSCOPE_API_KEY");  // 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
    private static String fileUrl = "https://your-audio-file-url";  // 请按实际情况进行替换
    private static String voiceId = "cosyvoice-v3-plus-myvoice-xxx"; // 请按实际情况进行替换
    private static final Logger logger = LoggerFactory.getLogger(Main.class);
    
    public static void main(String[] args)
            throws NoApiKeyException, InputRequiredException {
        VoiceEnrollmentService service = new VoiceEnrollmentService(apiKey);
        // 更新音色
        service.updateVoice(voiceId, fileUrl);
        logger.info("Update submitted. Request ID: {}", service.getLastRequestId());
    }
}
```

## RESTful API

#### **基本信息**

| URL | ``` https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization ``` |
| --- | --- |
| 请求方法 | POST |
| 请求头 | ``` Authorization: Bearer {api-key} // 需替换为您自己的API Key Content-Type: application/json ``` |
| 消息体 | 包含所有请求参数的消息体如下，对于可选字段，在实际业务中可根据需求省略： **重要** `model`为声音复刻模型，固定为`voice-enrollment`。 ``` { "model": "voice-enrollment", "input": { "action": "update_voice", "voice_id": "yourVoiceId", "url": "https://yourAudioFileUrl" } } ``` |

#### **请求参数**

**点击查看请求示例**

**重要**

`model`为声音复刻模型，固定为`voice-enrollment`。

```
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H "Content-Type: application/json" \
-d '{
    "model": "voice-enrollment",
    "input": {
        "action": "update_voice",
        "voice_id": "yourVoiceId",
        "url": "https://yourAudioFileUrl"
    }
}'
```

| **参数** | **类型** | **默认值** | **是否必须** | **说明** |
| --- | --- | --- | --- | --- |
| model | string | \\- | 是   | 声音复刻模型，固定为`voice-enrollment`。 |
| action | string | \\- | 是   | 操作类型，固定为`update_voice`。 |
| voice\\_id | string | \\- | 是   | 待更新的音色ID。 |
| url | string | \\- | 是   | 用于更新音色的音频文件URL。该URL要求公网可访问。 如何录制音频请参见[录音操作指南](https://help.aliyun.com/zh/model-studio/recording-guide)。 |

**点击查看响应示例**

```
{
    "output": {},
    "usage": {
        "count": 1
    },
    "request_id": "yourRequestId"
}
```

### **删除音色**

删除一个不再需要的音色以释放配额。此操作不可逆。

## Python SDK

#### **接口说明**

```
def delete_voice(self, voice_id: str) -> None:
    '''
    删除音色
    param: voice_id 需要删除的音色
    '''
```

#### **请求示例**

```
from dashscope.audio.tts_v2 import VoiceEnrollmentService

service = VoiceEnrollmentService()
service.delete_voice(voice_id='cosyvoice-v3-plus-myvoice-xxxxxxxx')
print(f"Deletion submitted. Request ID: {service.get_last_request_id()}")
```

## Java SDK

#### **接口说明**

```
/**
 * 删除音色
 *
 * @param voiceId 需要删除的音色
 * @throws NoApiKeyException 如果apikey为空
 * @throws InputRequiredException 如果必须参数为空
 */
public void deleteVoice(String voiceId) throws NoApiKeyException, InputRequiredException 
```

#### **请求示例**

```
import com.alibaba.dashscope.audio.ttsv2.enrollment.VoiceEnrollmentService;
import com.alibaba.dashscope.exception.InputRequiredException;
import com.alibaba.dashscope.exception.NoApiKeyException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Main {
    public static String apiKey = System.getenv("DASHSCOPE_API_KEY");  // 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
    private static String voiceId = "cosyvoice-v3-plus-myvoice-xxx"; // 请按实际情况进行替换
    private static final Logger logger = LoggerFactory.getLogger(Main.class);
    
    public static void main(String[] args)
            throws NoApiKeyException, InputRequiredException {
        VoiceEnrollmentService service = new VoiceEnrollmentService(apiKey);
        // 删除音色
        service.deleteVoice(voiceId);
        logger.info("Deletion submitted. Request ID: {}", service.getLastRequestId());
    }
}
```

## RESTful API

#### **基本信息**

| URL | ``` https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization ``` |
| --- | --- |
| 请求方法 | POST |
| 请求头 | ``` Authorization: Bearer {api-key} // 需替换为您自己的API Key Content-Type: application/json ``` |
| 消息体 | 包含所有请求参数的消息体如下，对于可选字段，在实际业务中可根据需求省略： **重要** `model`为声音复刻模型，固定为`voice-enrollment`。 ``` { "model": "voice-enrollment", "input": { "action": "delete_voice", "voice_id": "yourVoiceId" } } ``` |

#### **请求参数**

**点击查看请求示例**

**重要**

`model`为声音复刻模型，固定为`voice-enrollment`。

```
curl -X POST https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H "Content-Type: application/json" \
-d '{
    "model": "voice-enrollment",
    "input": {
        "action": "delete_voice",
        "voice_id": "yourVoiceId"
    }
}'
```

| **参数** | **类型** | **默认值** | **是否必须** | **说明** |
| --- | --- | --- | --- | --- |
| model | string | \\- | 是   | 声音复刻模型，固定为`voice-enrollment`。 |
| action | string | \\- | 是   | 操作类型，固定为`delete_voice`。 |
| voice\\_id | string | \\- | 是   | 待删除的音色ID。 |

**点击查看响应示例**

```
{
    "output": {},
    "usage": {
        "count": 1
    },
    "request_id": "yourRequestId"
}
```

## **音色配额与自动清理规则**

-   **总数限制**：1000个音色/账号
    
    > 当前接口不提供音色数量查询功能，可通过调用[查询音色列表](#401d33226330i)接口自行统计音色数目
    
-   **自动清理**：若单个音色在过去一年内未被用于任何语音合成请求，系统将自动将其删除
    

## **计费说明**

-   声音复刻：创建、查询、更新、删除音色免费
    
-   使用复刻生成的专属音色进行语音合成：按量（文本字符数）计费，参见[实时语音合成-CosyVoice/Sambert](https://help.aliyun.com/zh/model-studio/text-to-speech#992f46b0f4ha2)
    

## **版权与合法性**

您需对所提供声音的所有权及合法使用权负责，请注意阅读[服务协议](https://terms.alicdn.com/legal-agreement/terms/b_platform_service_agreement/20240229113512917/20240229113512917.html)。

## **错误码**

如遇报错问题，请参见[错误信息](https://help.aliyun.com/zh/model-studio/error-code)进行排查。

## **常见问题**

### **功能特性**

#### **Q：如何**调节自定义音色的语速、音量**？**

与使用预置音色完全相同。在调用语音合成API时，传入相应的参数即可，例如 `speech_rate` (Python) / `speechRate` (Java) 用于调节语速，`volume` 用于调节音量。详情请参见语音合成API文档（[Java SDK](https://help.aliyun.com/zh/model-studio/cosyvoice-java-sdk)/[Python SDK](https://help.aliyun.com/zh/model-studio/cosyvoice-python-sdk)/[WebSocket API](https://help.aliyun.com/zh/model-studio/cosyvoice-websocket-api)）

#### **Q：除了Java和Python，其他语言（如Go, C#, Node.js）如何调用？**

对于音色管理，请直接使用文档中提供的RESTful API。对于语音合成，请使用[WebSocket API](https://help.aliyun.com/zh/model-studio/cosyvoice-websocket-api)，并将复刻得到的 `voice_id` 作为 `voice` 参数传入。

### **故障排查**

如遇代码报错问题，请根据[错误码](#fe96688bd1l3n)中的信息进行排查。

#### **Q：**为什么找不到 VoiceEnrollmentService 类？

SDK版本过低。请[安装最新版SDK](https://help.aliyun.com/zh/model-studio/install-sdk)。

#### **Q：**声音复刻效果不佳，有杂音或不清晰怎么办**？**

这通常是由于输入音频质量不高导致的。请严格遵循[录音操作指南](https://help.aliyun.com/zh/model-studio/recording-guide)重新录制并上传音频。

### **权限与认证**

#### **Q：使用子业务空间的API Key是否可以进行声音复刻？**

需要为API Key对应的子业务空间进行[模型授权](https://help.aliyun.com/zh/model-studio/model-authentication-instructions)后方才支持，详情请参见[子业务空间的模型调用](https://help.aliyun.com/zh/model-studio/model-calling-in-sub-workspace)。
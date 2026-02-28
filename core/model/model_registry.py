"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 无外部依赖
Output: ModelConfig, ModelManager 模型配置和管理类
Pos: 核心模型注册中心，提供模型配置管理
"""

from dataclasses import dataclass
from typing import Dict, Optional, Literal
from enum import Enum
import json
from pathlib import Path


class BillingUnit(Enum):
    """计费单位枚举"""
    PER_IMAGE = "per_image"  # 按图片数量
    PER_SECOND = "per_second"  # 按秒数
    PER_MINUTE = "per_minute"  # 按分钟
    PER_HOUR = "per_hour"  # 按小时
    PER_1K_TOKENS = "per_1k_tokens"  # 按1K token
    PER_REQUEST = "per_request"  # 按请求次数
    PER_FRAME = "per_frame"  # 按帧数


class ModelProvider(Enum):
    """模型服务商枚举"""
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BAIDU = "baidu"
    TENCENT = "tencent"
    BYTEDANCE = "bytedance"
    BLACKFOREST = "black-forest-labs"


class ModelCategory(Enum):
    """模型类别枚举"""
    TEXT_TO_SPEECH = "text2speech"
    TEXT_TO_IMAGE = "text2image"
    IMAGE_TO_VIDEO = "image2video"
    TEXT_TO_VIDEO = "text2video"
    CHAT = "chat"
    EMBEDDING = "embedding"


@dataclass
class ModelConfig:
    """模型配置类"""
    name: str                        # 模型名称
    price: float                     # 价格
    billing_unit: BillingUnit        # 计费单位
    description: str                 # 描述
    provider: str                    # 所属公司/服务商
    category: str                    # 模型类别
    max_retries: int = 3            # 最大重试次数
    timeout: int = 30               # 超时时间
    enabled: bool = True            # 是否启用


class ModelManager:
    """模型配置管理器"""

    # todo csy 20250923:维护所有的属性，并且对照模型的实际参数看自动生成的是不是对的
    def __init__(self):
        self._models: Dict[str, Dict[str, ModelConfig]] = {
            # 文字转语音模型
            "text_to_speech": {
                "cosyvoice-v1": ModelConfig(
                    name="cosyvoice-v1",
                    price=0.2,
                    billing_unit=BillingUnit.PER_SECOND,
                    description="CosyVoice语音合成模型",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.TEXT_TO_SPEECH.value,
                    timeout=60,
                    enabled=False
                ),
                "sambert-zhichu-v1": ModelConfig(
                    name="sambert-zhichu-v1",
                    price=0.15,
                    billing_unit=BillingUnit.PER_SECOND,
                    description="SambertTTS中文语音合成",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.TEXT_TO_SPEECH.value,
                    timeout=45,
                    enabled=False
                )
            },

            # 文字转图片模型
            "text_to_image": {
                "qwen-image": ModelConfig(
                    name="qwen-image",
                    price=0.25,
                    billing_unit=BillingUnit.PER_IMAGE,
                    description="Qwen图像生成模型",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.TEXT_TO_IMAGE.value,
                    timeout=45,
                    enabled=False
                ),
                "wanx-v1": ModelConfig(
                    name="wanx-v1",
                    price=0.3,
                    billing_unit=BillingUnit.PER_IMAGE,
                    description="万象图像生成模型",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.TEXT_TO_IMAGE.value,
                    timeout=45,
                    enabled=False
                ),
                "flux-dev": ModelConfig(
                    name="flux-dev",
                    price=0.4,
                    billing_unit=BillingUnit.PER_IMAGE,
                    description="Flux高质量图像生成",
                    provider=ModelProvider.BLACKFOREST.value,
                    category=ModelCategory.TEXT_TO_IMAGE.value,
                    timeout=45,
                    enabled=False
                )
            },

            # 图片转视频模型
            "image_to_video": {
                "wan2.2-s2v": ModelConfig(
                    name="wan2.2-s2v",
                    price=1.5,
                    billing_unit=BillingUnit.PER_SECOND,
                    description="万象数字人视频生成",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.IMAGE_TO_VIDEO.value,
                    timeout=300,
                    enabled=False
                ),
                "cogvideox": ModelConfig(
                    name="cogvideox",
                    price=2.0,
                    billing_unit=BillingUnit.PER_SECOND,
                    description="CogVideoX视频生成",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.IMAGE_TO_VIDEO.value,
                    timeout=300,
                    enabled=False
                )
            },

            # 对话模型
            "chat": {
                "qwen-turbo": ModelConfig(
                    name="qwen-turbo",
                    price=2.0,
                    billing_unit=BillingUnit.PER_1K_TOKENS,
                    description="Qwen快速对话模型",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.CHAT.value,
                    timeout=30,
                    enabled=False
                ),
                "qwen-max": ModelConfig(
                    name="qwen-max",
                    price=8.0,
                    billing_unit=BillingUnit.PER_1K_TOKENS,
                    description="Qwen最强对话模型",
                    provider=ModelProvider.DASHSCOPE.value,
                    category=ModelCategory.CHAT.value,
                    timeout=30,
                    enabled=False
                )
            }
        }

    def get_model(self, category: str, model_name: str) -> Optional[ModelConfig]:
        """获取指定模型配置"""
        return self._models.get(category, {}).get(model_name)

    def get_models_by_category(self, category: str) -> Dict[str, ModelConfig]:
        """获取某类别的所有模型"""
        return self._models.get(category, {})

    def get_available_models(self, category: str) -> Dict[str, ModelConfig]:
        """获取某类别的可用模型"""
        models = self.get_models_by_category(category)
        return {name: config for name, config in models.items() if config.enabled}

    def calculate_cost(self, category: str, model_name: str, usage_amount: float) -> float:
        """计算使用成本"""
        model = self.get_model(category, model_name)
        if not model:
            raise ValueError(f"未找到模型: {category}/{model_name}")

        return model.price * usage_amount

    def add_model(self, category: str, model_config: ModelConfig):
        """添加新模型"""
        if category not in self._models:
            self._models[category] = {}
        self._models[category][model_config.name] = model_config

    def update_model_price(self, category: str, model_name: str, new_price: float):
        """更新模型价格"""
        model = self.get_model(category, model_name)
        if model:
            model.price = new_price

    def export_to_json(self, file_path: str):
        """导出配置到JSON文件"""
        data = {}
        for category, models in self._models.items():
            data[category] = {}
            for name, config in models.items():
                data[category][name] = {
                    "name": config.name,
                    "price": config.price,
                    "billing_unit": config.billing_unit.value,
                    "description": config.description,
                    "max_retries": config.max_retries,
                    "timeout": config.timeout,
                    "enabled": config.enabled
                }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# 使用追踪器记录使用情况
@dataclass
class UsageRecord:
    """使用记录"""
    category: str
    model_name: str
    usage_amount: float
    cost: float
    timestamp: str
    task_id: Optional[str] = None
    extra_info: Dict = None


class CostTracker:
    """成本追踪器"""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.usage_records: list[UsageRecord] = []

    def record_usage(self, category: str, model_name: str, usage_amount: float,
                     task_id: str = None, extra_info: Dict = None) -> float:
        """记录使用并计算成本"""
        from datetime import datetime

        cost = self.model_manager.calculate_cost(category, model_name, usage_amount)

        record = UsageRecord(
            category=category,
            model_name=model_name,
            usage_amount=usage_amount,
            cost=cost,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            extra_info=extra_info or {}
        )

        self.usage_records.append(record)
        return cost

    def get_total_cost(self, category: str = None) -> float:
        """获取总成本"""
        if category:
            return sum(r.cost for r in self.usage_records if r.category == category)
        return sum(r.cost for r in self.usage_records)

    def get_usage_summary(self) -> Dict:
        """获取使用汇总"""
        summary = {}
        for record in self.usage_records:
            key = f"{record.category}/{record.model_name}"
            if key not in summary:
                summary[key] = {"usage": 0, "cost": 0, "count": 0}

            summary[key]["usage"] += record.usage_amount
            summary[key]["cost"] += record.cost
            summary[key]["count"] += 1

        return summary


# 全局实例
model_manager = ModelManager()
cost_tracker = CostTracker(model_manager)


# 便捷的获取函数
def get_model_config(category: str, model_name: str) -> ModelConfig:
    """获取模型配置的便捷函数"""
    config = model_manager.get_model(category, model_name)
    if not config:
        raise ValueError(f"未找到模型配置: {category}/{model_name}")
    return config


def calculate_and_record_cost(category: str, model_name: str, usage_amount: float,
                              task_id: str = None) -> float:
    """计算并记录成本的便捷函数"""
    return cost_tracker.record_usage(category, model_name, usage_amount, task_id)


# 配置常量（用于代码中直接使用）
class ModelNames:
    """模型名称常量类"""

    class TextToSpeech:
        COSYVOICE_V1 = "cosyvoice-v1"
        SAMBERT_ZHICHU_V1 = "sambert-zhichu-v1"

    class TextToImage:
        QWEN_IMAGE = "qwen-image"
        WANX_V1 = "wanx-v1"
        FLUX_DEV = "flux-dev"

    class ImageToVideo:
        WAN2_2_S2V = "wan2.2-s2v"
        COGVIDEOX = "cogvideox"

    class Chat:
        QWEN_TURBO = "qwen-turbo"
        QWEN_MAX = "qwen-max"


class Categories:
    """类别名称常量"""
    TEXT_TO_SPEECH = "text_to_speech"
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_VIDEO = "image_to_video"
    CHAT = "chat"


# 使用示例
if __name__ == "__main__":
    # 获取模型配置
    tts_model = get_model_config(Categories.TEXT_TO_SPEECH, ModelNames.TextToSpeech.COSYVOICE_V1)
    print(f"TTS模型: {tts_model.name}, 价格: {tts_model.price}元/{tts_model.billing_unit.value}")

    # 记录使用并计算成本
    audio_duration = 15.5  # 15.5秒音频
    cost = calculate_and_record_cost(
        Categories.TEXT_TO_SPEECH,
        ModelNames.TextToSpeech.COSYVOICE_V1,
        audio_duration,
        task_id="task_001"
    )
    print(f"生成{audio_duration}秒音频，成本: {cost}元")

    # 记录图片生成成本
    image_count = 1
    cost = calculate_and_record_cost(
        Categories.TEXT_TO_IMAGE,
        ModelNames.TextToImage.QWEN_IMAGE,
        image_count,
        task_id="task_001"
    )
    print(f"生成{image_count}张图片，成本: {cost}元")

    # 获取总成本
    total_cost = cost_tracker.get_total_cost()
    print(f"总成本: {total_cost}元")

    # 获取使用汇总
    summary = cost_tracker.get_usage_summary()
    for model, stats in summary.items():
        print(f"{model}: 使用{stats['usage']}单位, 成本{stats['cost']:.2f}元, 调用{stats['count']}次")

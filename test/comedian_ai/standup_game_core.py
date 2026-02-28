"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：standup_game_core.py
"""

"""
AI脱口秀卡牌游戏 - 核心逻辑模块
提供可复用的游戏引擎，供测试和产品代码使用
"""

import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
import sys

from data import test_prompt

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from component.chat.chat import chat_with_model
from config.logging_config import get_logger


# ==================== 工具函数 ====================
def parse_option_from_response(ai_response: str, option_letter: str) -> Optional[str]:
    """
    从AI回复中解析出选项内容
    
    Args:
        ai_response: AI的完整回复
        option_letter: 选项字母 (A/B/C/D)
    
    Returns:
        选项的具体内容，如果解析失败返回None
    """
    lines = ai_response.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(f"{option_letter}."):
            # 移除 "A. " 部分，返回具体内容
            content = line[3:].strip()  # 跳过 "A. "
            return content
    return None


# ==================== 核心引擎类 ====================
class StandupGameEngine:
    """
    单口喜剧游戏引擎
    
    封装所有核心逻辑，包括：
    - 状态管理
    - Prompt生成
    - AI交互
    - 前提挖掘
    - 段子生成
    """
    
    def __init__(self):
        """初始化游戏引擎"""
        # 初始化 logger
        self.logger = get_logger(__name__)
        
        self.state = {
            "topic": None,           # 选择的主题
            "attitude": None,        # 选择的态度
            "premises": [],          # 已挖掘的前提（支持多轮）
            "conversation_history": [],  # 对话历史
            "rage_meter": 0,         # 怒气值（0-100）
            "max_rage": 100,         # 最大怒气值
            "rage_per_round": 20     # 每轮增加的怒气值
        }
        
        # 加载API配置
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置")
        
        self.logger.debug("🎮 游戏引擎初始化完成")
    
    def select_topic(self, topic: str):
        """
        选择主题
        
        Args:
            topic: 主题名称
        """
        self.state['topic'] = topic
        self.logger.info(f"📍 主题已选择: {topic}")
    
    def select_attitude(self, attitude: str):
        """
        选择态度
        
        Args:
            attitude: 态度名称
        """
        self.state['attitude'] = attitude
        self.logger.info(f"😤 态度已选择: {attitude}")
    
    def get_state(self) -> Dict:
        """
        获取当前状态
        
        Returns:
            当前游戏状态的副本
        """
        return self.state.copy()
    
    def can_generate_joke(self) -> bool:
        """
        判断是否可以生成段子
        
        Returns:
            True if 至少挖掘了1轮前提
        """
        return len(self.state['premises']) >= 1
    
    def get_rage_meter(self) -> int:
        """
        获取当前怒气值
        
        Returns:
            当前怒气值
        """
        return self.state['rage_meter']
    
    def is_rage_full(self) -> bool:
        """
        判断怒气值是否已满
        
        Returns:
            True if 怒气值达到最大值
        """
        return self.state['rage_meter'] >= self.state['max_rage']
    
    def increase_rage(self):
        """
        增加怒气值（每完成一轮前提挖掘调用）
        """
        old_rage = self.state['rage_meter']
        self.state['rage_meter'] = min(
            self.state['rage_meter'] + self.state['rage_per_round'],
            self.state['max_rage']
        )
        new_rage = self.state['rage_meter']
        self.logger.debug(f"🔥 怒气值变化: {old_rage} → {new_rage}")
        
        if self.is_rage_full():
            self.logger.info("⚡ 怒气值已满！终结技已解锁！")
    
    def _get_system_prompt(self, stage: str) -> str:
        """
        根据不同阶段返回system prompt
        
        Args:
            stage: "premise" | "punchline"
        
        Returns:
            system prompt字符串
        """
        base_prompt = """
            你是一位单口喜剧创作教练，帮助用户创作段子, 在这个过程中完成用户情绪与心理的疏导。
            核心理论：
            - 段子 = 铺垫（主题+态度+前提）+ 包袱（呈现/混合）
            - 前提要具体、有共鸣、不能讲故事
            - 包袱要用"呈现"（模仿表演）或"混合"（行业对比）
            - 好的段子来自真实、具体的细节，尤其是对话、表情、动作
            """
        
        if stage == "premise":
            premises_text = "\n".join([f"  - {p}" for p in self.state['premises']]) if self.state['premises'] else "  （尚未挖掘）"
            round_num = len(self.state['premises']) + 1
            
            # 根据轮数调整追问策略
            if round_num == 1:
                guidance = """【第1轮目标】锁定“爆点场景”
                - 选项要是具体的“事件”，不是问题
                - 每个选项都是一个完整的“槽点场景”
                - 例如：“安检员要求我把电脑开机证明不是炸弹”
                - 选项设计：A=最常见、B=有点夹张、C=冷门但真实
                """
            elif round_num == 2:
                guidance = """【第2轮目标】挖掘“荒谬行为”
                - 选项要描述“对方做了什么蠢事”
                - 带上动作、表情的细节
                - 例如：“他眨着眼睛看屏幕，像在等包裹出生”
                - 选项要有“画面感”，让用户能回忆起来
                """
            elif round_num == 3:
                guidance = """【第3轮目标】抓取“对话/表情”（黄金素材）
                - 选项必须包含“具体的话”（用引号）
                - 每个选项是不同的“对话版本”
                - 例如：“他问我：‘东二环是哪个方向？’”
                - 选项要有“口音/语气”的暗示
                """
            elif round_num == 4:
                guidance = """【第4轮目标】挖掘“你的反应”
                - 选项要描述“你当时怎么回答/反应的”
                - 带上你的情绪（耐心/无奈/崩溃）
                - 例如：“我强忍着说：‘师傅您就往东开！’”
                - 选项要形成“递进感”（A耐心、B无奈、C崩溃）
                """
            else:
                guidance = f"""【第{round_num}轮目标】深挖“反转细节”
                - 选项要描述“然后发生了什么更崩溃的”
                - 或“你最终怎么吐槽的”
                - 选项要有“结果/后续”
                - 如果已有足够素材，可以暗示笑点方向
                """
            
            return base_prompt + f"""
                当前状态：
                - 主题：{self.state['topic']}
                - 态度：{self.state['attitude']}
                - 当前是第{round_num}轮挖掘
                - 已挖掘前提：
                {premises_text}
                
                {guidance}
                
                ====================  选项设计原则 ====================
                
                【核心思路】选项不是问题，是具体的“答案预设”
                
                1. 【选项 = 具体场景/行为/对话】
                   - 不要：“他做了什么？”（太宽泛）
                   - 要：“他拿着手机给自己的车导航”（具体画面）
                
                2. 【选项要有“暗示性”】
                   - 帮助用户回忆起真实的细节
                   - 通过对比让用户选“最接近的那个”
                   - 例如：
                     A. 他眨着眼看屏幕（常见）
                     B. 他不断回头问我（有点夹张）
                     C. 他直接把手机给我让我导航（冷门但真实）
                
                3. 【选项要形成“细节链”】
                   - 第1轮：大场景 → 第2轮：具体行为 → 第3轮：对话内容
                   - 每轮选项都基于上一轮的选择
                   - 例如：
                     第1轮选了：“司机不看导航一直问我”
                     第2轮选项就要围绕：“他具体问了什么”
                
                4. 【选项长度和风格】
                   - 第1-2轮：10-18字（描述行为/场景）
                   - 第3轮起：包含引号对话，可以稍长
                   - 语气：口语化，像朋友聊天
                   - 可以加语气词：“吧”、“对吧”、“的那种”
                
                5. 【选项要有“对比度”】
                   - A/B/C 三个选项要有区分度
                   - 不要三个意思差不多的选项
                   - 让用户能明确感知“我的情况是哪个”
                
                ====================  问题设计原则 ====================
                
                1. 【问题要有“引导性”】
                   - 不要：“然后呢？”（太开放）
                   - 要：“他当时具体说了什么话？”（明确指向）
                
                2. 【问题可以带调侃/共情】
                   - 第1轮：“我猜...是不是这种情况？”
                   - 第2轮：“然后他做了什么让你更崩溃的？”
                   - 第3轮：“我已经能想象他的表情了，他具体说了什么？”
                   - 第4轮起：“你当时怎么回的？忍住没笑吧？”
                
                3. 【问题要简短有力】
                   - 不要长篇大论
                   - 一句话，直接问到点上
                
                ====================  输出要求 ====================
                
                请严格按以下格式输出：
                
                问题：[一句话的追问，带点共情/调侃]
                
                A. [具体场景/行为/对话，10-20字]
                B. [具体场景/行为/对话，10-20字]
                C. [具体场景/行为/对话，10-20字]
                D. 手动输入你的答案
                
                注意：
                - A/B/C 必须是“陈述句”，不是问句
                - 每个选项都要能直接作为“前提”记录
                - D 选项固定为“手动输入你的答案”
                """
        
        elif stage == "punchline_actout":
            context = "\n".join([f"  {i+1}. {p}" for i, p in enumerate(self.state['premises'])])
            return base_prompt + f"""
                当前状态：
                - 主题：{self.state['topic']}
                - 态度：{self.state['attitude']}
                - 已挖掘前提细节：
                {context}
                
                任务：使用【呈现 (Act-out)】技巧生成一个完整的单口喜剧段子。
                ==================== 核心原则 ====================
                1. 【笑点前置】第一句话就要抓住观众
                2. 【节奏感】铺垫-包袱交替，不要平铺直叙
                3. 【画面感】让观众脑海里有画面，像看电影
                4. 【真实感】必须基于已挖掘的前提，不许编造
        
                ==================== 结构设计 ====================
        
                【开场钩子】（1句话，抓注意力）
                - 用"最荒谬的点"开场，不要铺垫背景
                - 例子：
                  ✅ "我遇到过一个司机，他问我东二环在哪。"
                  ❌ "我上周打车的时候，遇到了一件事..."（太平淡）
        
                【铺垫】（2-3句，快速建立场景）
                - 用短句，营造节奏感
                - 每句话都要有"信息增量"
                - 适当加态度词（"简直了"、"你敢信？"）
        
                【呈现/表演】（核心部分，3-5个来回对话）
                - 模仿对方的话（要有口音/语气/停顿）
                - 你的回应要有"递进感"（从耐心→无奈→崩溃）
                - 重复对方的愚蠢行为，每次重复加一层荒谬
                - 格式：
                  他：（模仿语气）"XXX"
                  我："XXX"
                  他：（继续蠢）"XXX"
                  我："XXX！"（情绪升级）
        
                【反转/升华】（最后1-2句，点题）
                - 用夸张比喻收尾（"我怀疑他的驾照是..."）
                - 或用反问句（"你说这不是XXX吗？"）
                - 要有"画龙点睛"的效果
        
                ==================== 语言技巧 ====================
                1. 【口语化】像聊天，不要像写作文
                   - 多用"你知道吗"、"简直了"、"我的天"
                   - 可以用不完整的句子（"他，那个表情..."）
        
                2. 【节奏控制】
                   - 短句制造紧张：3个短句 → 1个长句
                   - 用"然后"、"结果"制造转折
        
                3. 【夸张但不过分】
                   - 基于真实细节夸张（"他瞪大眼睛，跟见鬼似的"）
                   - 不要编造情节（"然后他突然跳车了"）
        
                4. 【互动感】
                   - 适当加观众预期："你猜他说什么？"
                   - 模仿时可以加舞台提示：（学他的样子）
        
                ==================== 反面案例（禁止） ====================
                ❌ 平铺直叙："他不认识路，我很生气。"
                ❌ 过度解释："因为他是司机，所以应该认识路。"
                ❌ 假大空："这个社会就是这样..."
                ❌ 讲故事："从那以后我再也不..."
        
                ==================== 输出要求 ====================
                - 直接输出段子，不要任何前缀（"段子如下："）
                - 不要分段标注（"铺垫："、"包袱："）
                - 总长度：150-250字
                - 对话用引号，舞台提示用括号
        
                开始创作！记住：让观众笑，不是让观众懂道理。
                """
        
        elif stage == "punchline_mix":
            context = "\n".join([f"  {i+1}. {p}" for i, p in enumerate(self.state['premises'])])
            return base_prompt + f"""
                当前状态：
                - 主题：{self.state['topic']}
                - 态度：{self.state['attitude']}
                - 已挖掘前提细节：
                {context}
                
                任务：使用【混合 (Mix)】技巧生成一个完整的单口喜剧段子。
                ==================== 混合技巧核心 ====================
                【原理】将荒谬的事，放到另一个场景，通过"反差"放大笑点
                【关键】类比的行业要有"专业门槛"，反差才明显
        
                ==================== 结构设计 ====================
        
                【开场+铺垫】（2-3句，快速陈述原始槽点）
                - 直接说荒谬的事
                - 不要细节，点到为止
                - 例子："司机不认路，还问我东二环在哪。"
        
                【类比引入】（1句，建立联想）
                - 用"这就好比..."开头
                - 选择反差强的行业（医生、厨师、飞行员、法官）
                - 例子："这就好比我去了个餐厅..."
        
                【平行复现】（3-5句，用同样逻辑演绎）
                - 把原始场景的"逻辑漏洞"平移到新场景
                - 保持结构一致（问题→回答→更蠢的问题）
                - 用对话形式，让类比生动
                - 格式：
                  我："XXX"（正常需求）
                  对方："XXX？"（荒谬反问）
                  我："对啊。"（解释）
                  对方："XXX！"（更荒谬）
        
                【反转收尾】（1-2句，点题）
                - 用反问句强化荒谬感
                - 可以把两个场景对比（"XX不会X，XX不认X"）
                - 例子："你说这不是扯吗！"
        
                ==================== 行业选择指南 ====================
                根据原始槽点选择最佳类比：
                - 不认路/不专业 → 医生/厨师/律师（强专业门槛）
                - 推卸责任 → 消防员/警察（职责清晰）
                - 反复确认/磨叽 → 飞行员/外科医生（需要果断）
                - 装懂/瞎指挥 → 导演/指挥家（需要权威）
        
                ==================== 语言技巧 ====================
                1. 【类比要精准】
                   - 找"对应关系"：司机的导航 = 厨师的菜谱
                   - 不要生硬联想
        
                2. 【保持口语化】
                   - 像讲故事，不要像写议论文
                   - "你想想"、"你说"、"这不是..."
        
                3. 【夸张收尾】
                   - 最后可以加一句全局性吐槽
                   - "我看他俩是一块儿从火星来的"
        
                ==================== 输出要求 ====================
                - 直接输出段子，不要标注
                - 总长度：120-200字
                - 类比要自然，不要太跳跃
        
                开始创作！记住：类比越荒谬，笑点越强。
                """
        
        return base_prompt
    
    def _chat(self, user_input: str, stage: str) -> str:
        """
        调用AI进行对话
        
        Args:
            user_input: 用户输入
            stage: 当前阶段 ("premise" | "punchline")
        
        Returns:
            AI的回复内容
        """
        self.logger.debug(f"🤖 开始调用 AI (stage={stage})")
        # self.logger.debug(f"📤 用户输入: {user_input[:100]}...")  # 截取前100字符
        self.logger.debug(f"📤 用户输入: {user_input}...")
        
        # 构建消息
        messages = [
            {"role": "system", "content": self._get_system_prompt(stage)}
        ]
        
        # 添加对话历史（保持上下文）
        messages.extend(self.state['conversation_history'])
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        self.logger.debug(f"📨 消息数量: {len(messages)} 条")
        
        # 调用AI
        try:
            # qwen
            # response = chat_with_model(
            #     api_key=self.api_key,
            #     model_type="qwen",
            #     model="qwen-max",
            #     messages=messages
            # )
            # deepseek
            response = chat_with_model(
                api_key=self.api_key,
                messages=messages,
                model_type="deepseek",
                model="deepseek-v3.2",
                extra_body={"enable_thinking": True},
            )
            
            self.logger.debug(f"📥 AI 响应长度: {len(response)} 字符")
            # self.logger.debug(f"📥 AI 响应内容:\n{response[:200]}...")  # 前200字符
            self.logger.debug(f"📥 AI 响应内容:\n{response}...")  # 前200字符
            
            # 更新对话历史
            self.state['conversation_history'].append({"role": "user", "content": user_input})
            self.state['conversation_history'].append({"role": "assistant", "content": response})
            
            self.logger.debug(f"💾 对话历史已更新，当前条数: {len(self.state['conversation_history'])}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ AI 调用失败: {e}")
            raise
    
    def start_mining_round(self) -> str:
        """
        开始一轮前提挖掘，获取AI的追问和选项
        
        Returns:
            AI生成的追问和选项
        """
        round_num = len(self.state['premises']) + 1
        self.logger.info(f"⛏️  开始第 {round_num} 轮前提挖掘")
        
        ai_response = self._chat("继续追问细节", "premise")
        
        self.logger.debug(f"✅ 第 {round_num} 轮追问生成完成")
        return ai_response
    
    def process_user_choice(self, user_choice: str, ai_response: str, custom_input: str = None) -> Dict:
        """
        处理用户选择，记录前提，并增加怒气值
        
        Args:
            user_choice: 用户选择 ("A" | "B" | "C" | "D")
            ai_response: AI的回复（用于解析选项）
            custom_input: 如果选择D，需要提供自定义输入
        
        Returns:
            {
                "success": True/False,
                "recorded_premise": "记录的前提内容" or None,
                "error_message": "错误信息" or None,
                "rage_meter": 当前怒气值,
                "rage_full": 是否已满
            }
        """
        self.logger.debug(f"👤 用户选择: {user_choice}")
        
        if user_choice == 'D':
            # 自定义输入
            if custom_input and custom_input.strip():
                premise = custom_input.strip()
                self.state['premises'].append(premise)
                self.increase_rage()  # 增加怒气值
                self.logger.info(f"📝 记录自定义前提: {premise}")
                return {
                    "success": True,
                    "recorded_premise": premise,
                    "error_message": None,
                    "rage_meter": self.get_rage_meter(),
                    "rage_full": self.is_rage_full()
                }
            else:
                self.logger.warning("⚠️  自定义输入为空")
                return {
                    "success": False,
                    "recorded_premise": None,
                    "error_message": "自定义输入不能为空",
                    "rage_meter": self.get_rage_meter(),
                    "rage_full": self.is_rage_full()
                }
        elif user_choice in ['A', 'B', 'C']:
            # 解析并记录选项
            self.logger.debug(f"🔍 开始解析选项 {user_choice}")
            option_content = parse_option_from_response(ai_response, user_choice)
            if option_content:
                self.state['premises'].append(option_content)
                self.increase_rage()  # 增加怒气值
                self.logger.info(f"📝 记录前提 [{user_choice}]: {option_content}")
                return {
                    "success": True,
                    "recorded_premise": option_content,
                    "error_message": None,
                    "rage_meter": self.get_rage_meter(),
                    "rage_full": self.is_rage_full()
                }
            else:
                # 解析失败，使用默认记录
                fallback = f"选项{user_choice}的内容"
                self.state['premises'].append(fallback)
                self.increase_rage()  # 增加怒气值
                self.logger.warning(f"⚠️  选项 {user_choice} 解析失败，使用 fallback: {fallback}")
                return {
                    "success": True,
                    "recorded_premise": fallback,
                    "error_message": "解析失败，使用默认记录",
                    "rage_meter": self.get_rage_meter(),
                    "rage_full": self.is_rage_full()
                }
        else:
            self.logger.error(f"❌ 无效的选项: {user_choice}")
            return {
                "success": False,
                "recorded_premise": None,
                "error_message": f"无效的选项: {user_choice}",
                "rage_meter": self.get_rage_meter(),
                "rage_full": self.is_rage_full()
            }
    
    def get_punchline_options(self) -> Dict:
        """
        获取终结技选项（橙卡）
        
        Returns:
            {
                "option_1": {"name": "拟态面具", "description": "...", "type": "act_out"},
                "option_2": {"name": "维度裂缝", "description": "...", "type": "mix"}
            }
        """
        self.logger.info("🎴 获取橙卡选项")
        
        if not self.is_rage_full():
            self.logger.error("❌ 怒气值未满，无法获取终结技")
            raise ValueError("怒气值未满，无法获取终结技选项")
        
        options = {
            "option_1": {
                "name": "拟态面具",
                "description": "直接模仿那个愚蠢的瞬间（呈现技巧 Act-out）",
                "type": "act_out",
                "icon": "🎭"
            },
            "option_2": {
                "name": "维度裂缝",
                "description": "如果这事儿发生在别的行业...（混合技巧 Mix）",
                "type": "mix",
                "icon": "🌀"
            }
        }
        
        self.logger.debug(f"🎴 橙卡选项: {list(options.keys())}")
        return options
    
    def generate_joke_with_actout(self) -> str:
        """
        使用【呈现技巧】生成段子
        
        Returns:
            生成的段子文本
        """
        self.logger.info("🎭 开始生成段子 - 呈现技巧")
        self.logger.debug(f"📋 当前前提数量: {len(self.state['premises'])}")
        
        if not self.can_generate_joke():
            self.logger.error("❌ 前提不足，无法生成段子")
            raise ValueError("至少需要挖掘1轮前提才能生成段子")
        
        joke = self._chat(
            "请使用'呈现'技巧，模仿那个愚蠢的瞬间，生成段子",
            "punchline_actout"
        )
        
        self.logger.info(f"✅ 段子生成完成 (长度: {len(joke)} 字符)")
        return joke
    
    def get_mix_options(self) -> List[str]:
        """
        获取混合技巧的对比行业选项
        
        Returns:
            行业列表
        """
        return [
            "医生/医院",
            "厨师/餐厅",
            "教师/学校",
            "程序员/公司",
            "快递员/物流"
        ]
    
    def generate_joke_with_mix(self, target_industry: str = None) -> str:
        """
        使用【混合技巧】生成段子（旧版本，一步生成）
        
        Args:
            target_industry: 目标对比行业（可选，AI会自动选择合适的）
        
        Returns:
            生成的段子文本
        """
        self.logger.info("🌀 开始生成段子 - 混合技巧")
        self.logger.debug(f"🏭 目标行业: {target_industry if target_industry else 'AI自动选择'}")
        self.logger.debug(f"📋 当前前提数量: {len(self.state['premises'])}")
        
        if not self.can_generate_joke():
            self.logger.error("❌ 前提不足，无法生成段子")
            raise ValueError("至少需要挖掘1轮前提才能生成段子")
        
        user_input = "请使用'混合'技巧，将这个情况类比到另一个行业，生成段子"
        if target_industry:
            user_input += f"\n类比行业：{target_industry}"
        
        joke = self._chat(user_input, "punchline_mix")
        
        self.logger.info(f"✅ 段子甞成完成 (长度: {len(joke)} 字符)")
        return joke
    
    def generate_joke_with_mix_v2(self, target_industry: str = None) -> dict:
        """
        使用【混合技巧】两阶段生成段子
        
        Args:
            target_industry: 目标对比行业（可选）
        
        Returns:
            {
                "stage1_draft": "第一阶段基础版",
                "stage2_enhanced": "第二阶段强化版",
                "selected_industry": "选择的行业"
            }
        """
        if not self.can_generate_joke():
            self.logger.error("❌ 前提不足，无法生成段子")
            raise ValueError("至少需要挖掘1轮前提才能生成段子")
        
        self.logger.info("🌀 开始两阶段混合技巧生成")
        
        # ===== 第一阶段：基础类比结构 =====
        self.logger.info("📝 第一阶段：生成基础类比结构")
        
        stage1_result = self._chat(
            self._build_stage1_mix_prompt(target_industry),
            "punchline_mix_stage1"
        )
        
        # 解析第一阶段输出（假设格式：行业|段子文本）
        if "|" in stage1_result:
            selected_industry, stage1_draft = stage1_result.split("|", 1)
            selected_industry = selected_industry.strip()
            stage1_draft = stage1_draft.strip()
        else:
            selected_industry = target_industry or "未知"
            stage1_draft = stage1_result
        
        self.logger.info(f"✅ 第一阶段完成，选择行业: {selected_industry}")
        self.logger.debug(f"第一阶段段子长度: {len(stage1_draft)}")
        
        # ===== 第二阶段：喜剧强化 =====
        self.logger.info("🎨 第二阶段：喜剧强化改写")
        
        stage2_enhanced = self._chat(
            self._build_stage2_enhance_prompt(stage1_draft, selected_industry),
            "punchline_mix_stage2"
        )
        
        self.logger.info(f"✅ 第二阶段完成，最终段子长度: {len(stage2_enhanced)}")
        
        return {
            "stage1_draft": stage1_draft,
            "stage2_enhanced": stage2_enhanced,
            "selected_industry": selected_industry
        }
    
    def generate_joke(self) -> str:
        """
        生成最终的单口喜剧段子（默认使用呈现技巧）
        已废弃：请使用 generate_joke_with_actout() 或 generate_joke_with_mix()
        
        Returns:
            生成的段子文本
        """
        joke = self.generate_joke_with_actout()

        # Define punchline_promote_prompt - assuming it's a constant or derived
        # For now, using a placeholder string. This should be properly defined.
        punchline_promote_prompt = "你是一位单口喜剧大师，请对以下段子进行润色，让它更具喜剧效果和包袱。请保持其核心内容不变，只在表达上进行加强。"

        self.logger.info(f"✨ 正在对段子进行喜剧强化...")
        messages = [
            {"role": "system", "content": punchline_promote_prompt},
            {"role": "user", "content": joke},
        ]
        punchline_promoted = chat_with_model(
            api_key=self.api_key,
            messages=messages,
            model_type="deepseek",
            model="deepseek-v3.2",
            extra_body={"enable_thinking": True},
        )
        joke = punchline_promoted

        self.logger.info(f"✅ 段子生成完成 (长度: {len(joke)} 字符)")
        return joke
    
    def get_premises_count(self) -> int:
        """
        获取已挖掘的前提数量
        
        Returns:
            前提数量
        """
        return len(self.state['premises'])
    
    def get_premises(self) -> List[str]:
        """
        获取所有已挖掘的前提
        
        Returns:
            前提列表
        """
        return self.state['premises'].copy()
    
    def _select_key_premises(self) -> List[str]:
        """
        从所有前提中精选2-3个最有笑点的
        
        Returns:
            精选后的前提列表
        """
        all_premises = self.state['premises']
        
        # 如果前提少于3个，全部使用
        if len(all_premises) <= 3:
            return all_premises
        
        # 简单打分：包含引号+5分，包含"问"+3分，包含动作词+2分
        scored_premises = []
        for p in all_premises:
            score = 0
            if '"' in p or '“' in p or "'" in p:
                score += 5
            if '问' in p or '说' in p:
                score += 3
            if any(word in p for word in ['个', '看', '指', '翻', '等', '盯']):
                score += 2
            scored_premises.append((score, p))
        
        # 按分数排序，取前3个
        scored_premises.sort(reverse=True, key=lambda x: x[0])
        selected = [p for _, p in scored_premises[:3]]
        
        self.logger.debug(f"从 {len(all_premises)} 条前提中精选了 {len(selected)} 条")
        
        return selected
    
    def _build_stage1_mix_prompt(self, target_industry: str = None) -> str:
        """构建第一阶段提示词：基础类比结构"""
        
        # 选择使用的前提（精选2-3个最荒谬的）
        selected_premises = self._select_key_premises()
        premises_text = "\n".join([f"  {i+1}. {p}" for i, p in enumerate(selected_premises)])
        
        prompt = f"""你现在要用"混合技巧"创作段子的【基础版】。

当前状态：
- 主题：{self.state['topic']}
- 态度：{self.state['attitude']}
- 核心前提（已精选最荒谬的2-3条）：
{premises_text}

================== 第一阶段任务 ==================

创作一个"基础类比段子"，只需要：
1. 开场铺垫（1句话陈述原始槽点）
2. 类比引入（"这就好比..."）
3. 平行复现（用新行业重现原始逻辑漏洞）
4. 简单收尾（1句话吐槽）

================== 行业选择指南 ==================

【优先级排序】
1. 首选（安全、日常、不涉及生死）：
   - 厨师/餐厅、理发师、修电脑/手机、装修工、游戏策划、快递员
   
2. 可用但需谨慎（确保幻想化、夸张化）：
   - 医生：只能写"问诊奇葩"，不能写手术/开刀
   - 飞行员：只能写"不认航线"，不能写坠机风险
   - 法官：只能写"搞混卷宗"，不能写冤案

3. 尽量避免：
   - 任何会让人联想到"真实生死事故"的场景

【风险红线】
- 不要让类比职业出现"真的要闹出人命"的场景
- 医疗/飞行类，必须明显是"夸张幻想"，不能写实
- 整体基调是"无奈地笑"，不是"越想越害怕"
"""

        if target_industry:
            prompt += f"\n用户指定行业：{target_industry}"
        
        prompt += """

================== 前提使用指南 ==================

不要机械复述所有前提，只选择上面【核心前提】中的细节：
- 优先使用那些"荒谬感最强"的对话或动作
- 在类比场景里，用类似结构复现这些逻辑漏洞

例如：
- 原：司机"个着导航像等包裹" → 类比：厨师"盯着菜谱像看天书"
- 原：司机"问东二环在哪" → 类比：厨师"问宫保鸡丁有没有鸡"

================== 输出要求 ==================

格式：[行业名称]|[段子文本]

例如：
厨师/餐厅|这司机太离谱了，明明有导航还问我路。这就好比我去了个餐厅...

注意：
- 字数：100-150字
- 语言：口语化，但不要堆码太多梗
- 对话：有1-2处即可，不要太多
- 这是基础版，不要过度夸张
"""
        
        return prompt
    
    def _build_stage2_enhance_prompt(self, stage1_draft: str, industry: str) -> str:
        """构建第二阶段提示词：喜剧强化"""
        
        prompt = f"""你现在要对一个段子进行"喜剧强化改写"。

【第一阶段基础版】
{stage1_draft}

【类比行业】
{industry}

================== 第二阶段任务 ==================

在保持结构和行业不变的前提下，增强喜剧效果：

1. 【增加口语化标记】
   - 加入"我去""大哥""简直了"等自然口语
   - 但不要每句话都加

2. 【强化对话节奏】
   - 如果有对话，可以增加1-2轮来回
   - 让"愚蠢感"通过对话递进展现
   - 模仿原声语气（迷惑、茫然、理直气壮）

3. 【加一个夸张比喻或反转】
   - 在合适位置加1个夸张比喻
   - 或在收尾时加一个小反转/吐槽

4. 【控制梗的数量】
   - 整个段子中，明显的"包袱/大梗"控制在2~3个
   - 不要句句抖包袱，保持呼吸感

================== 风格边界（重要）==================

在增强笑点时，请注意：
- ❌ 不要把类比职业写得像真的要闹出人命
- ❌ 医疗、飞行场景，不要描写具体手术/事故过程
- ❌ 不要加入血腥、恐怖、让人不适的细节
- ✅ 整体基调是"无奈地笑"，不是"越想越害怕"
- ✅ 夸张是可以的，但要明显是幻想/玩笑

例如：
- ✅ "我怀疑他的驾照是彩票刮出来的"
- ❌ "我怕他真的会撞车害死我"

================== 输出要求 ==================

- 直接输出强化后的段子，不要前缀说明
- 字数：150-250字（比第一阶段稍长，但不要超过300）
- 保持第一阶段的行业和结构，只做强化
- 如果第一阶段已经很好，不要画蛇添足
"""
        
        return prompt

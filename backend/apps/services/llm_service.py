import json
import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from django.conf import settings

# 引入 tenacity 进行优雅的自动重试
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# --- Pydantic Models ---
class UserIntentAnalysis(BaseModel):
    intent_type: str = Field(description="用户意图分类: CHAT, QUERY_TREATMENT, CRISIS_ALERT, QUERY_POLICY")
    symptoms: List[str] = Field(description="从用户输入中提取的症状列表，如 ['考前失眠']", default_factory=list)
    problem_name: Optional[str] = Field(description="提取的核心心理问题名称（如果存在）", default=None)

class AICard(BaseModel):
    type: str = Field(description="卡片类型: TREATMENT, POLICY, ARTICLE")
    title: str = Field(description="卡片标题")
    content: str = Field(description="卡片核心内容展示")
    extra_info: Optional[dict] = Field(description="额外键值对数据", default=None)

class LLMResponse(BaseModel):
    content: str = Field(description="给用户的共情和自然语言回复")
    cards: List[AICard] = Field(description="提取出来的结构化卡片列表", default_factory=list)

class LLMService:
    """
    封装与大模型交互逻辑（意图识别、最终生成）。
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'LLM_API_KEY', '')
        self.base_url = getattr(settings, 'LLM_BASE_URL', '')
        self.model_name = getattr(settings, 'LLM_MODEL_NAME', '')
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _clean_json_string(self, raw_str: str) -> str:
        """清洗大模型输出的 JSON 字符串"""
        # 使用正则表达式移除 Markdown 代码块标记 (```json ... ```)
        backticks = "`" * 3
        pattern = r"^" + backticks + r"(?:json)?\n|" + backticks + r"$"
        cleaned = re.sub(pattern, "", raw_str.strip(), flags=re.MULTILINE | re.IGNORECASE)
        # 移除控制字符，防止 JSON loads 报错
        cleaned = re.sub(r'[\x00-\x1F\x7F]', '', cleaned)
        return cleaned

    def _truncate_context(self, context_data: dict, max_length: int = 6000) -> str:
        """上下文防溢出保护：防止图谱数据过大撑爆 Token 限制"""
        if not context_data:
            return "没有找到相关的图谱背景知识。"
        
        context_str = json.dumps(context_data, ensure_ascii=False)
        if len(context_str) > max_length:
            logger.warning(f"Graph context too long ({len(context_str)} chars), truncating to {max_length}.")
            # 简单截断并补齐，防止 JSON 完全破坏
            return context_str[:max_length] + '... [内容已截断]'
        return context_str

    # 遇到超时、限流、API错误时，采用指数退避算法重试（重试3次）
    @retry(
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    def analyze_intent(self, user_input: str, history: list = None) -> UserIntentAnalysis:
        """调用 LLM 识别用户意图并提取症状和问题名称。"""
        system_prompt = """你是一个校园心理辅助咨询系统的意图识别核心模块。你的任务是从用户的输入（及历史记录）中抽取关键的诊断信息和意图类型。

### 🚨 核心判定准则 (Critical)
1. **情感/压力/困扰优先**：只要出现描述心理状态、人际冲突、考试压力、失眠、情绪波动等具体“困扰”的内容，必须判定为 `QUERY_TREATMENT`。
2. **拒绝过度判定为 CHAT**：除非用户只是在说“你好”、“哈哈”、“吃了没”等纯社交或日常无关废话，否则严禁归类为 `CHAT`。
3. **结合历史上下文**：如果当前输入只有“我该怎么办”、“还有吗”、“什么方法”等代词或短语，必须通过 [对话历史] 追溯用户正在讨论的问题，并将其填入 `problem_name`。
4. **名词对齐（Hints）**：系统图谱中存在以下标准名称，请在提取 `problem_name` 时尽量靠近它们：
   - 「期末挂科极度焦虑」、「考研压力」、「严重人际冲突」、「宿舍严重人际冲突」、「社交焦虑」、「情绪抑郁与绝望危机」。

意图类型定义：
- CRISIS_ALERT: 用户表达了自残、自杀、极度绝望或伤害他人的意愿。这是最高优先级。
- QUERY_TREATMENT: 用户描述了具体困扰（如失眠、宿舍关系焦虑、失恋），并希望获得帮助或方法。
- QUERY_POLICY: 用户询问有关校园政策、缓考、教务流程等。
- CHAT: 纯粹的寒暄或日常问候。

必须返回且仅返回如下格式的 JSON 字符串：
{
    "intent_type": "CHAT/QUERY_TREATMENT/CRISIS_ALERT/QUERY_POLICY",
    "symptoms": ["症状1", "症状2"],
    "problem_name": "通过当前句或上下文推导出的核心问题名称"
}"""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # 注入对话历史供模型补全意图
            if history:
                for msg in history:
                    messages.append({"role": msg['role'], "content": msg['content']})
            
            messages.append({"role": "user", "content": f"请结合历史（若有）分析此输入并返回 JSON：\n{user_input}"})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0, 
            )
            
            # 记录 Token 消耗
            usage = response.usage
            logger.info(f"[Token Audit] analyze_intent used {usage.total_tokens} tokens")
            
            raw_content = response.choices[0].message.content
            content = self._clean_json_string(raw_content)
            
            try:
                return UserIntentAnalysis.model_validate_json(content)
            except ValidationError as ve:
                logger.error(f"Intent Validation Error: {str(ve)}. Raw content: {raw_content}")
                # 尝试再次解析（兼容某些模型多嵌套一层的错误）
                data = json.loads(content)
                if isinstance(data, dict) and "intent_type" not in data:
                    # 寻找可能嵌套的键
                    for val in data.values():
                        if isinstance(val, dict) and "intent_type" in val:
                            return UserIntentAnalysis(**val)
                raise ve
            
        except Exception as e:
            logger.error(f"Error during intent analysis: {str(e)}")
            return UserIntentAnalysis(intent_type="CHAT", symptoms=[])

    @retry(
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    def generate_response(self, user_input: str, graph_context: dict, history: list = None) -> LLMResponse:
        """生成带有温暖共情文本与翻译后的结构化卡片 JSON。"""
        system_prompt = """你是 SH MindStation 心理健康助手。基于[检索到的参考知识]提取客观信息并返回 JSON。

### 🚨 绝对核心指令：卡片下发策略 (Selection Strategy)
你必须根据用户的**当前具体诉求**，从[参考知识]中选择性地生成 `cards`。严禁一次性堆砌所有卡片！
1. **按需下发**：
   - 只有当用户询问“怎么做”、“什么方法”、“求助”或首次描述痛苦时，才生成 `TREATMENT` 卡片。
   - 只有当用户明确询问“规定”、“流程”、“手续”、“换宿”、“部门”时，才生成 `POLICY` 卡片。
   - `ARTICLE` 作为补充阅读，仅在用户表现出对某种心理知识的渴求时才酌情下发（最多 1 张）。
2. **上下文关联**：结合 [对话历史]，如果用户当前的追问很具体（如“那怎么换宿呢？”），则仅下发对应的政策卡片，不要再次下发之前的治疗方案。

### [卡片数据“翻译”规则]
图谱提供的 `treatments` 等干预方案包含学术临床用语。你在生成 JSON 的 `cards` 时，绝对禁止直接复制粘贴学术原话！
你必须将概念“翻译”成通俗、温暖、面向大学生的【1-2-3 具体操作步骤】，并使用 \n 换行。

### [提取与映射规则]
1. 治疗方案 (TREATMENT)：
   - `title`: 简短的方案名称。
   - `content`: 翻译后的具体操作步骤（3-5步）。
2. 校园政策 (POLICY)：
   - `title`: 明确的政策名。
   - `content`: 关键规章条款。
   - `extra_info`: 包含 {"org": "部门名称", "location": "办公地点"}。
3. 心理文章 (ARTICLE)：
   - `title`: 文章标题。
   - `content`: 标注为“作者：xxx”。
   - `extra_info`: 包含 {"image": "封面图链接", "id": "uuid"}。

### [对话准则]
- 文本回复 (`content` 字段) 应包含共情、肯定和对下发卡片的简单引导说明。
- 即使没有匹配的卡片，也必须返回 JSON 结构（cards 可为空列表 []）。
- 严禁药物推荐，严禁医疗诊断。"""
        
        # 使用防溢出截断
        context_str = self._truncate_context(graph_context)
        
        format_example = {
            "content": "听到你描述的状态我深感理解。这里有一些小练习你可以试一试...",
            "cards": [
                {
                    "type": "TREATMENT",
                    "title": "深呼吸平复小练习",
                    "content": "1. 找个安静的地方坐下。\n2. 吸气4秒。\n3. 呼气6秒。",
                    "extra_info": {}
                }
            ]
        }
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n[参考知识]\n{context_str}\n\n必须严格按此 JSON 格式返回:\n{json.dumps(format_example, ensure_ascii=False)}"}
        ]
        
        # 注入历史记录 (最近的对话上下文)
        if history:
            for msg in history:
                messages.append({"role": msg['role'], "content": msg['content']})
        
        # 追加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.6,
                max_tokens=1500
            )
            
            # 记录 Token 消耗
            usage = response.usage
            logger.info(f"[Token Audit] generate_response used {usage.total_tokens} tokens (Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens})")
            
            clean_json = self._clean_json_string(response.choices[0].message.content)
            
            try:
                return LLMResponse.model_validate_json(clean_json)
            except ValidationError as ve:
                logger.error(f"Pydantic Validation Error: {str(ve)}. Raw: {clean_json}")
                data = json.loads(clean_json)
                return LLMResponse(**data)
                
        except Exception as e:
             logger.error(f"Error generating response: {str(e)}")
             return LLMResponse(content="抱歉同学，系统遇到些网络波动。如果感到严重不适，请立刻联系辅导员或拨打校园心理热线。")

llm_service = LLMService()

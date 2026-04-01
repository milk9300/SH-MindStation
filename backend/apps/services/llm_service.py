import json
import logging
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError, model_validator
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from django.conf import settings

# 引入 tenacity 进行优雅的自动重试
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# --- Pydantic Models ---
class UserIntentAnalysis(BaseModel):
    intent_type: str = Field(description="用户意图分类: CHAT, QUERY_TREATMENT, CRISIS_ALERT, QUERY_POLICY")
    symptoms: List[str] = Field(description="从用户输入中提取的症状列表", default_factory=list)
    problem_name: Optional[str] = Field(description="提取的核心心理问题名称", default=None)

class InitialLLMResponse(BaseModel):
    """互动 RAG 第一阶段：共情回复 + 选项提议"""
    intent_type: str = "CHAT"
    empathy_reply: str = Field(default="我非常理解你的感受，能再跟我多说一点吗？", description="温暖且共情的开场白")
    options: List[Dict[str, Any]] = Field(description="从候选列表中挑选出的匹配项，包含 uuid 和 name", default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def fallback_fields(cls, data):
        if isinstance(data, dict):
             if not data.get('empathy_reply'):
                 data['empathy_reply'] = data.get('content') or data.get('reply') or ""
             if not data.get('intent_type'):
                 data['intent_type'] = "CHAT"
        return data

class LLMCard(BaseModel):
    """图谱结构化卡片定义"""
    type: str  # TREATMENT, POLICY, CRISIS, ARTICLE
    title: str
    content: str = "" # 允许为空，并在解析时尝试从其它字段填充
    extra_info: dict = {}

    @model_validator(mode='before')
    @classmethod
    def flexible_mapping(cls, data):
        if isinstance(data, dict):
             # 自动将 explanation, method, description 映射到 content
             if not data.get('content'):
                 data['content'] = data.get('explanation') or data.get('method') or data.get('description') or ""
        return data

class LLMResponse(BaseModel):
    """大模型最终回复定义"""
    content: str
    structured_cards: List[LLMCard] = Field(default_factory=list)

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
        """强化版 JSON 提取逻辑：从杂乱文本中精准提取第一个层级的 JSON 对象"""
        if not raw_str: return "{}"
        
        # 1. 移除 Markdown 代码块标记 (```json ... ```)
        cleaned = re.sub(r"```(?:json)?\n?|```$", "", raw_str.strip(), flags=re.MULTILINE | re.IGNORECASE)
        
        # 2. 从第一个 { 到最后一个 } 截取
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
            
        # 3. 移除危险的控制字符
        cleaned = re.sub(r'[\x00-\x1F\x7F]', '', cleaned)
        return cleaned

    def _truncate_context(self, context_data: dict, max_length: int = 8000) -> str:
        """上下文防溢出保护：防止图谱数据过大撑爆 Token 限制。"""
        if not context_data:
            return "没有找到相关的图谱背景知识。"
        
        try:
            context_str = json.dumps(context_data, ensure_ascii=False)
            if len(context_str) <= max_length:
                return context_str
            
            # 启发式截断
            temp_data = json.loads(context_str) 
            if 'articles' in temp_data:
                for art in temp_data['articles']:
                    if 'content' in art and len(art['content']) > 200:
                        art['content'] = art['content'][:200] + "... (截断)"
            
            context_str = json.dumps(temp_data, ensure_ascii=False)
            if len(context_str) > max_length:
                pruned_data = {
                    "treatments": temp_data.get("treatments", [])[:5],
                    "articles": temp_data.get("articles", [])[:5],
                    "campus_policies": temp_data.get("campus_policies", [])[:3]
                }
                context_str = json.dumps(pruned_data, ensure_ascii=False)
            
            return context_str
        except Exception as e:
            logger.error(f"Error during context truncation: {str(e)}")
            return "图谱背景知识提取异常。"

    @retry(
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    def analyze_intent(self, user_input: str, history: List[Dict] = None) -> UserIntentAnalysis:
        """调用 LLM 识别用户意图。"""
        logger.info(f"[Intent Audit] Analyzing: {user_input[:40]}")
        
        system_prompt = """你是一个专业的心理咨询助手。请从用户输入中提取意图、症状和核心问题名称。

核心问题标准库 (problem_name 必须从以下选择，不可编造):
- 科研倦怠: (导师压力、实验室、科研论文、任务重)
- 学业压力: (挂科焦虑、GPA绩点、考试不顺)
- 宿舍人际压力: (同学关系、霸凌、孤立)
- 失恋心理创伤: (分手、情感破裂)
- 情绪内耗: (焦虑、抑郁、失眠)

必须返回 JSON 格式：
{
    "intent_type": "QUERY_TREATMENT/QUERY_POLICY/CRISIS_ALERT/CHAT",
    "symptoms": ["症状点1", "症状点2"],
    "problem_name": "核心问题库中的名称"
}"""
        
        default_result = UserIntentAnalysis(intent_type="CHAT", symptoms=[], problem_name=None)
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            if history: messages.extend(history)
            messages.append({"role": "user", "content": f"分析并返回 JSON：\n{user_input}"})
            
            # 彻底清洗消息，防止 API Gateway 注入或历史遗留 tool_calls 导致 400 错误
            clean_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
            ]
            
            logger.debug(f"[LLM Debug] Clean Messages: {json.dumps(clean_messages, ensure_ascii=False)}")
            # 彻底清洗消息，彻底移除 tool_calls 干扰
            clean_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=clean_messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            raw_content = response.choices[0].message.content
            logger.info(f"[LLM Debug] Raw Result: {raw_content}")
            content = self._clean_json_string(raw_content)
            try:
                data = json.loads(content)
                # 兼容格式
                if "intent_type" not in data:
                    for val in data.values():
                        if isinstance(val, dict) and "intent_type" in val:
                            data = val
                            break
                return UserIntentAnalysis(**data)
            except Exception as pe:
                logger.error(f"Intent JSON parse failed: {pe}. Content: {content}")
                return default_result
        except Exception as e:
            logger.error(f"Intent LLM error: {e}")
            return default_result

    @retry(
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    def get_empathy_and_options(self, user_input: str, candidates: List[Dict], history: List[Dict] = None) -> InitialLLMResponse:
        """
        [交互 RAG 第一阶段]
        识图意图，生成共情回复，并从向量检索出的候选节点中挑选最匹配的。
        """
        system_prompt = f"""你是一个专业的校园心理咨询助手。
你的任务是：
1. 分析用户意图 (CHAT, QUERY_TREATMENT, QUERY_POLICY, CRISIS_ALERT)。
2. 生成 2-3 句温暖、共情且不带评判的回复。
3. 从提供的 [候选节点(Candidates)] 列表中，挑选出 1-3 个最贴切用户当前状态的项。

[候选节点(Candidates)]:
{json.dumps(candidates, ensure_ascii=False)}

必须极严格地返回以下 JSON 格式：
{{
    "intent_type": "CHAT",
    "empathy_reply": "我能感受到你现在的压力...",
    "options": [
        {{"uuid": "...", "name": "..."}}
    ]
}}

注意：
- 严禁随意编造 Candidates 列表以外的 UUID 或名称。
- 如果没有合适的匹配项，options 可以为空列表。
"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            if history: messages.extend(history)
            messages.append({"role": "user", "content": f"分析并返回 JSON：\n{user_input}"})
            
            clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=clean_messages,
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            logger.info(f"[LLM Debug Stage 1] Raw Result: {response.choices[0].message.content}")
            content = self._clean_json_string(response.choices[0].message.content)
            try:
                return InitialLLMResponse.model_validate_json(content)
            except Exception as ve:
                logger.warning(f"InitialLLMResponse validation failed: {ve}. Trying manual parse.")
                data = json.loads(content)
                # 兼容不同层级
                if "intent_type" not in data:
                    for val in data.values():
                        if isinstance(val, dict) and "intent_type" in val:
                            data = val; break
                return InitialLLMResponse(**data)
        except Exception as e:
            logger.error(f"Empathy and options generation error: {e}")
            return InitialLLMResponse(intent_type="CHAT", empathy_reply="我能感受到你现在比较困扰，能具体跟我说说吗？", options=[])

    @retry(
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True
    )
    def generate_response(self, user_input: str, graph_context: dict, history: list = None) -> LLMResponse:
        """生成回复。"""
        system_prompt = """你现在是 SH MindStation 的 AI 心理咨询师。
请基于提供的 [参考知识] 生成 JSON 格式的回复：
- content: 简短(2-3句)，共情且接纳，引出卡片。
- structured_cards: 将 [参考知识] 中的条目转为对应的卡片列表。
- 严禁空穴来风，严禁伪造不存在的 UUID 或 URL。

卡片映射规则:
1. treatments -> title: name, content: 说明, type: TREATMENT
2. campus_policies -> title: name, content: content, type: POLICY
3. articles -> title: name, content: 简介, type: ARTICLE, extra_info: {image: cover, id: uuid}"""
        
        context_str = self._truncate_context(graph_context)
        
        messages = [
            {"role": "system", "content": f"{system_prompt}\n\n[参考知识]\n{context_str}"}
        ]
        if history: messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        
        # 彻底清洗消息，防止 400 错误
        clean_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=clean_messages,
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = self._clean_json_string(response.choices[0].message.content)
            try:
                return LLMResponse.model_validate_json(content)
            except:
                data = json.loads(content)
                return LLMResponse(content=data.get("content", ""), structured_cards=data.get("structured_cards", []))
        except Exception as e:
            logger.error(f"Generate response error: {e}")
            return LLMResponse(content="我出了一点小错，请稍后再试。", structured_cards=[])

llm_service = LLMService()

import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

# Pydantic Model for Intent Extraction Output
class UserIntentAnalysis(BaseModel):
    intent_type: str = Field(description="用户意图分类: CHAT(日常吐槽), QUERY_TREATMENT(寻求干预/解决方案), CRISIS_ALERT(高危预警/可能伤害自己或他人), QUERY_POLICY(查询政策)")
    symptoms: List[str] = Field(description="从用户输入中提取的症状列表，如 ['考前失眠', '焦虑', '自杀倾向']", default_factory=list)
    problem_name: Optional[str] = Field(description="提取的核心心理问题名称（如果存在），如 '期末挂科极度焦虑'", default=None)

class AICard(BaseModel):
    type: str = Field(description="卡片类型: TREATMENT (治疗方案), POLICY (校园政策), ARTICLE (素材文章)")
    title: str = Field(description="卡片标题")
    content: str = Field(description="卡片核心内容展示")
    extra_info: Optional[dict] = Field(description="额外键值对数据，如 { 'org': '教务处' }", default=None)

class LLMResponse(BaseModel):
    content: str = Field(description="给用户的共情和自然语言回复（纯文本，不要包含卡片里的细节）")
    cards: List[AICard] = Field(description="提取出来的结构化卡片列表", default_factory=list)

class LLMService:
    """
    封装与大模型交互逻辑（意图识别、最终生成）。
    """
    
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def analyze_intent(self, user_input: str) -> UserIntentAnalysis:
        """
        调用 LLM 识别用户意图并提取症状和问题名称。
        采用 JSON schema 的方式强制 LLM 输出结构化结果。
        """
        system_prompt = """
        你是一个校园心理辅助咨询系统的意图识别核心模块。你的任务是从学生的输入中抽取关键的诊断信息和意图类型。

        意图类型定义：
        - CRISIS_ALERT: 用户表达了自残、自杀、极度绝望或伤害他人的意愿。这是最高优先级。
        - QUERY_TREATMENT: 用户描述了具体困扰（如失眠、焦虑），并希望获得帮助或方法。
        - QUERY_POLICY: 用户询问有关校园政策、缓考、教务流程等。
        - CHAT: 普通的吐槽、寒暄或日常对话，没有明显的核心心理诉求。

        提取规范：
        1. 症状 (symptoms): 必须是原子化的、通用的症状核心词，如 ["失眠", "心慌", "焦虑", "自残", "反复检查"]。不要提取过于口语化的长句。
        2. 心理问题 (problem_name): 宏观概括。示例参考: '期末挂科极度焦虑', '人际关系冲突', '社交恐惧', '抑郁倾向'。

        示例：
        输入："我最近快考试了，整晚睡不着，感觉要是挂科我就完了，真想一了百了"
        输出：{"intent_type": "CRISIS_ALERT", "symptoms": ["考前失眠", "自杀意图", "学业压力"], "problem_name": "期末挂科极度焦虑"}

        输入："怎么申请缓考啊？"
        输出：{"intent_type": "QUERY_POLICY", "symptoms": [], "problem_name": "缓考申请问题"}
        """
        
        try:
            messages = [
                {"role": "system", "content": system_prompt + "\n\n请只返回符合下面描述的 JSON 字符串，不要包含任何额外的markdown语法或解释：\n" + json.dumps(UserIntentAnalysis.model_json_schema())},
                {"role": "user", "content": user_input}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0,  # 使用 0.0 保证提取稳定性
            )
            
            content = response.choices[0].message.content
            analysis = UserIntentAnalysis.model_validate_json(content)
            return analysis
            
        except Exception as e:
            logger.error(f"Error during intent analysis: {str(e)}")
            # Fail-fast with a safe default
            return UserIntentAnalysis(intent_type="CHAT", symptoms=[])

    def generate_response(self, user_input: str, graph_context: dict) -> LLMResponse:
        """
        根据用户的输入和检索到的图谱上下文（结构化 JSON树），生成结构化的回复。
        """
        system_prompt = """
你是 SH MindStation 心理健康助手。基于[检索到的参考知识]提取客观信息并返回 JSON。

[提取规则]
1. 治疗方案：将 `treatments` 列表映射为 `type: "TREATMENT"` 的卡片。
   - `title`: 方案名称 (name)。
   - `content`: 结合方案原理 (rationale) 和 `skills` 下技巧的名称与步骤。
2. 校园政策：将 `campus_context` 映射为 `type: "POLICY"` 的卡片。
   - `title`: 政策名称 (policy_name)。
   - `content`: 政策事项 (policy_detail)。
   - `extra_info`: 包含 {"org": "部门名称", "location": "办公地点"}。

[对话准则]
- `content` 字段仅用于情感共情和简短引导，不要罗列数据。
- 即使没有知识，也必须返回 JSON 结构（cards 可为空）。
- 严禁药物推荐，严禁医疗诊断。
"""
        
        context_str = json.dumps(graph_context, ensure_ascii=False) if graph_context else "没有找到相关的图谱背景知识。"
        
        format_example = {
            "content": "听到你描述的状态我深感理解，这里有一些专业建议...",
            "cards": [
                {
                    "type": "TREATMENT",
                    "title": "方案名称",
                    "content": "基于某原理，建议尝试某技巧：具体步骤...",
                    "extra_info": {}
                },
                {
                    "type": "POLICY",
                    "title": "政策名称",
                    "content": "政策具体说明",
                    "extra_info": {"org": "教务处", "location": "行政楼"}
                }
            ]
        }
        
        messages = [
            {"role": "system", "content": system_prompt + f"\n\n[检索到的参考知识]\n{context_str}\n\n你必须严格按此 JSON 格式返回:\n" + json.dumps(format_example, ensure_ascii=False)},
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500
            )
            content_json = response.choices[0].message.content
            # Remove control characters that break JSON parsing
            import re
            clean_json = re.sub(r'[\x00-\x1F\x7F]', '', content_json)
            try:
                data = json.loads(clean_json)
                return LLMResponse.model_validate(data)
            except Exception as e:
                logger.error(f"JSON Parse Error: {str(e)}. Raw: {clean_json}")
                raise e
        except Exception as e:
             logger.error(f"Error generating response: {str(e)}")
             return LLMResponse(content="抱歉同学，系统遇到些网络延迟。如果感到严重不适，请立刻拨打校园 24 小时心理干预热线。")

llm_service = LLMService()

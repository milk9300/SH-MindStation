import logging
from django.db import transaction
from apps.models import ChatSession, ChatMessage, CrisisAlertLog
from apps.services.llm_service import llm_service
from apps.services.graph_service import graph_service

logger = logging.getLogger(__name__)

class ChatService:
    """
    核心流转：接收对话 -> 调用 LLM 识图意图 -> 调用图谱查数据 -> 调用 LLM 生成回复。
    The RAG Pipeline.
    """
    
    @transaction.atomic
    def process_message(self, user, session_id, content: str) -> dict:
        """
        处理用户的单次聊天请求，串联所有子服务。
        """
        # 1. 记录用户的原始输入
        session, created = ChatSession.objects.get_or_create(
            id=session_id,
            defaults={'user': user, 'title': content[:20] + '...'}
        )
        
        user_message = ChatMessage.objects.create(
            session=session,
            role="user",
            content=content
        )

        # 2. 调用 LLM 服务进行意图与实体识别
        intent = llm_service.analyze_intent(content)
        
        # 3. 尝试进行图谱检索，获取 RAG Context
        # ★ 注意这里：将 content 作为第二个参数传入，供查询政策等兜底使用
        graph_context = graph_service.fetch_context_for_intent(intent, content)
        
        # 4. 图谱安全拦截（检查返回的树中是否有高危预警）
        is_high_risk = False
        emergency_action = None
        
        if graph_context and "symptoms" in graph_context:
            for symptom in graph_context["symptoms"]:
                if symptom.get("risk_info"):
                    # 发现高危症状，触发熔断
                    is_high_risk = True
                    risk_info = symptom["risk_info"]
                    emergency_action = risk_info.get("action", "系统检测到极度危险，请拨打24小时干预热线: 400-xxx-xxxx")
                    
                    # 写高危审计日志
                    CrisisAlertLog.objects.create(
                        user=user,
                        message=user_message,
                        risk_level=risk_info.get("level", "极高"),
                        trigger_symptom=symptom.get("name")
                    )
                    break
                    
        # 5. 回复与审计策略
        # 如果图谱没有识别到具体节点，但 LLM 识别出了意图，也要记录预案
        if not is_high_risk and intent.intent_type == "CRISIS_ALERT":
             is_high_risk = True
             # 写高危审计日志（语义识别触发）
             CrisisAlertLog.objects.create(
                 user=user,
                 message=user_message,
                 risk_level="极高",
                 trigger_symptom=f"LLM 语义识别: {intent.symptoms[0] if intent.symptoms else '未提取具体症状'}"
             )

        # 6. 生成回复策略
        if is_high_risk or intent.intent_type == "CRISIS_ALERT":
            # 【熔断机制】如果检测到危机，严禁调用 LLM 生成，直接返回静态应急预案
            final_reply = emergency_action if emergency_action else "同学，系统检测到您当前可能处于极度痛苦中。生命非常宝贵，请立即拨打校园 24 小时心理危机干预热线: 400-xxx-xxxx。会有专业的老师全天候陪伴您度过难关。"
            # 统一卡片格式
            ai_structured_cards = [{
                "type": "CRISIS",
                "title": "紧急干预资源",
                "content": final_reply,
                "extra_info": {"level": "极高", "location": "校医院心理科/校保卫处"}
            }]
        else:
            # 普通的 RAG 生成模式，调用 LLM 获取结构化响应
            llm_res = llm_service.generate_response(content, graph_context)
            final_reply = llm_res.content
            
            # 将 LLM 提取的卡片转化为数据库存储格式
            ai_structured_cards = [card.model_dump() for card in llm_res.cards]
            
        # 6. 入库系统回复
        ai_message = ChatMessage.objects.create(
            session=session,
            role="ai",
            content=final_reply,
            structured_cards=ai_structured_cards,
            intent_type=intent.intent_type
        )
        
        return {
            "session_id": str(session.id),
            "reply": final_reply,
            "structured_cards": ai_structured_cards,
            "intent": intent.model_dump()
        }

chat_service = ChatService()

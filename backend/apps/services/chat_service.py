import logging
from django.db import transaction
from django.conf import settings
from apps.models import ChatSession, ChatMessage, CrisisAlertLog
from apps.services.llm_service import llm_service
from apps.services.graph_service import graph_service
from apps.services.crisis_service import crisis_interceptor

logger = logging.getLogger(__name__)

class ChatService:
    """
    核心流转：接收对话 -> 调用 LLM 识图意图 -> 调用图谱查数据 -> 调用 LLM 生成回复。
    The RAG Pipeline.
    """
    
    @transaction.atomic
    def process_message(self, user, session_id, content: str, selected_node_uuid: str = None) -> dict:
        """
        处理用户的单次聊天请求，支持分阶段交互。
        1. 危机拦截
        2. 若有 selected_node_uuid -> 深度检索并生成最终卡片 (Stage 2)
        3. 若为普通文字 -> 向量候选 + LLM 共情并提供选项 (Stage 1)
        """
        # 1. 记录会话与原始输入
        session, created = ChatSession.objects.get_or_create(
            id=session_id,
            defaults={'user': user, 'title': content[:20] + '...'}
        )
        
        user_message = ChatMessage.objects.create(
            session=session,
            role="user",
            content=content or f"[Selection] {selected_node_uuid}"
        )

        # 0. 毫秒级硬拦截 (Hard Circuit Breaker)
        crisis_check = crisis_interceptor.fast_check(content)
        if crisis_check:
            ai_structured_cards = crisis_check["structured_cards"]
            self._fix_card_urls(ai_structured_cards)
            
            ai_message = ChatMessage.objects.create(
                session=session,
                role="ai",
                content=crisis_check["reply"],
                structured_cards=ai_structured_cards,
                intent_type="CRISIS_ALERT"
            )
            
            CrisisAlertLog.objects.get_or_create(
                message=user_message,
                defaults={
                    "user": user,
                    "risk_level": "极高危",
                    "trigger_symptom": "正则硬命中"
                }
            )
            
            return {
                "session_id": str(session.id),
                "reply": crisis_check["reply"],
                "structured_cards": ai_structured_cards,
                "intent": {"intent_type": "CRISIS_ALERT"}
            }

        # 2. 获取历史上下文
        recent_messages = ChatMessage.objects.filter(session=session).order_by('-created_at')[:6]
        history_list = [
            {"role": "assistant" if m.role == "ai" else m.role, "content": m.content} 
            for m in reversed(recent_messages) if m.id != user_message.id
        ]

        # --- 策略 A: 用户已经点击了选项 (Deep RAG Stage 2) ---
        if selected_node_uuid:
            logger.info(f"[RAG Stage 2] Fetching deep context for UUID: {selected_node_uuid}")
            graph_context = graph_service.fetch_deep_context(selected_node_uuid)
            ai_structured_cards = []
            final_reply = "抱歉，我没有找到相关的图谱资料。"
            
            if graph_context:
                problem_name = graph_context.get("problem_name", "这个问题")
                final_reply = f"关于“{problem_name}”，我为你找到了一些可能有帮助的信息："
                
                for plan in graph_context.get("emergency_plans", []):
                    ai_structured_cards.append({
                        "type": "CRISIS", "title": plan.get("title", ""),
                        "content": plan.get("content", ""),
                        "extra_info": {"contacts": plan.get("contacts", "")}
                    })
                
                for t in graph_context.get("treatments", []):
                    ai_structured_cards.append({
                        "type": "TREATMENT", "title": t.get("name", ""),
                        "content": t.get("content") or t.get("method", ""),
                        "extra_info": {"method": t.get("method", "")}
                    })
                    
                for p in graph_context.get("policies", []):
                    ai_structured_cards.append({
                        "type": "POLICY", "title": p.get("name", ""),
                        "content": p.get("content", ""),
                        "extra_info": {"department": p.get("department", "")}
                    })
                    
                for a in graph_context.get("articles", []):
                    ai_structured_cards.append({
                        "type": "ARTICLE", "title": a.get("name", ""),
                        "content": a.get("summary", ""),
                        "extra_info": {"id": a.get("uuid", ""), "image": a.get("cover", ""), "url": a.get("url", "")}
                    })
            self._fix_card_urls(ai_structured_cards)
            
            ChatMessage.objects.create(
                session=session,
                role="ai",
                content=final_reply,
                structured_cards=ai_structured_cards,
                intent_type="QUERY_TREATMENT"
            )
            
            return {
                "session_id": str(session.id),
                "reply": final_reply,
                "structured_cards": ai_structured_cards,
                "stage": "FINAL"
            }

        # --- 策略 B: 普通文本对话 (Empathy + Options Stage 1) ---
        # 1. 向量混合检索候选
        candidates = graph_service.find_candidates(content, top_k=5)
        
        # 2. LLM 生成共情并从中挑选
        initial_res = llm_service.get_empathy_and_options(content, candidates, history=history_list)
        
        final_reply = initial_res.empathy_reply
        options = initial_res.options  # 这里的 options 会包含 [{uuid, name}, ...]
        
        ChatMessage.objects.create(
            session=session,
            role="ai",
            content=final_reply,
            structured_cards=[], # 选项不入库为卡片，前端根据 options 渲染
            intent_type=initial_res.intent_type
        )
        
        return {
            "session_id": str(session.id),
            "reply": final_reply,
            "options": options,
            "stage": "RECOMMEND"
        }

    def _fix_card_urls(self, cards):
        if not cards: return
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
        def _fix(obj):
            if isinstance(obj, list):
                for item in obj: _fix(item)
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ['cover', 'image', 'avatar'] and isinstance(v, str):
                        if v and not v.startswith(('http')):
                            obj[k] = f"{backend_url}/{v.lstrip('/')}"
                    else: _fix(v)
        _fix(cards)

chat_service = ChatService()

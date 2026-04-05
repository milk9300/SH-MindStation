import logging
from django.db import transaction
from django.conf import settings
from django.core.cache import cache
from apps.models import ChatSession, ChatMessage, CrisisAlertLog
from apps.services.llm_service import llm_service
from apps.services.graph_service import graph_service
from apps.services.crisis_service import crisis_interceptor

logger = logging.getLogger(__name__)

class ChatService:
    """
    RAG Pipeline v2: 基于槽位状态的动态 Agent 咨询流水线。
    利用 Redis 管理会话状态，实现多次追问直至收集足够信息，再推荐图谱资源。
    """

    def _get_session_slots(self, session_id: str) -> dict:
        """从 Redis 获取会话的槽位状态"""
        key = f"chat_slots_{session_id}"
        return cache.get(key, {"event": None, "duration": None, "impact": None})

    def _update_session_slots(self, session_id: str, new_slots: dict, current_slots: dict):
        """更新 Redis 中的槽位状态"""
        key = f"chat_slots_{session_id}"
        updated = current_slots.copy()
        
        # 只更新有值且不是 None/空字符串 的槽位
        if isinstance(new_slots, dict):
            for k, v in new_slots.items():
                if v and str(v).strip() and str(v).lower() != "null":
                    updated[k] = v
                    
        cache.set(key, updated, timeout=86400) # 过期时间 24 小时
        return updated

    @transaction.atomic
    def process_message(self, user, session_id, content: str, selected_node_uuid: str = None) -> dict:
        """
        处理用户的单次聊天请求，支持分阶段交互。
        Stage 1: 槽位追问 (Slot Collection) -> 循环至填满
        Stage 2: 资源推荐 (Option Recommendation) -> 提供图谱候选项
        Stage 3: 深度检索 (Deep RAG) -> 用户点击选项后，返回结构化卡片
        """
        # 1. 记录会话与原始输入
        session, created = ChatSession.objects.get_or_create(
            id=session_id,
            defaults={'user': user, 'title': content[:20] if content else '咨询会话'}
        )
        
        # 优化：如果用户是点击选项进入，我们先尝试获取节点名称，让聊天记录更自然
        display_content = content
        if not content and selected_node_uuid:
            try:
                from apps.repositories.neo4j_repo import neo4j_repo
                with neo4j_repo.driver.session() as s_node:
                    n_res = s_node.run("MATCH (n {uuid: $uuid}) RETURN n.`名称` as name", uuid=selected_node_uuid).single()
                    if n_res:
                        display_content = f"我想了解：{n_res['name']}"
                    else:
                        display_content = "[选择建议]"
            except:
                display_content = "[选择建议]"

        user_message = ChatMessage.objects.create(
            session=session,
            role="user",
            content=display_content
        )

        # [NEW] 异步画像记录：异步提取症状并累加隐式分值
        from apps.tasks import async_profile_user
        async_profile_user.delay(user.id, session_id, display_content, message_id=user_message.id)

        # 0. 安全风险拦截与分级干预 (Tiered Safety Intervention)
        crisis_check = crisis_interceptor.fast_check(content)
        if crisis_check:
            ai_structured_cards = crisis_check["structured_cards"]
            self._fix_card_urls(ai_structured_cards)
            
            # A. 无论是否拦截，都要记录预警日志 (Audit Always)
            # 这里的 trigger_symptom 我们记录前 20 个字
            CrisisAlertLog.objects.create(
                user=user,
                message=user_message,
                risk_level=crisis_check["hit_level"],
                trigger_symptom=f"命中关键词: {content[:20]}...",
                status=CrisisAlertLog.StatusChoices.PENDING
            )

            # B. 策略判定：如果是高优/极高危，执行硬拦截 (Hard Intercept)
            if crisis_check.get("should_interrupt"):
                logger.warning(f"Hard Intercept triggered for Level: {crisis_check['hit_level']}")
                
                ChatMessage.objects.create(
                    session=session,
                    role="ai",
                    content=crisis_check["reply"],
                    structured_cards=ai_structured_cards,
                    intent_type="CRISIS_ALERT"
                )
                
                # 清空普通会话槽位，防止危机解除后逻辑错乱
                cache.delete(f"chat_slots_{session_id}")
                
                return {
                    "session_id": str(session.id),
                    "reply": crisis_check["reply"],
                    "structured_cards": ai_structured_cards,
                    "intent": {"intent_type": "CRISIS_ALERT"}
                }
            
            # C. 如果是中低危，执行静默干预 (Soft Intervention / Shadow Cards)
            # 我们不中断后续 LLM 流程，但将拦截到的卡片作为“影子数据”传递给后续流程展示
            # 注：这里可以先暂存，在最终返回前合并到 reply 中
            logger.info(f"Soft Intervention triggered for Level: {crisis_check['hit_level']}")
            shadow_intervention = {
                "reply_prefix": crisis_check["reply"],
                "cards": ai_structured_cards
            }
        else:
            shadow_intervention = None

        # 获取历史上下文
        recent_messages = ChatMessage.objects.filter(session=session).order_by('-created_at')[:6]
        history_list = [
            {"role": "assistant" if m.role == "ai" else m.role, "content": m.content} 
            for m in reversed(recent_messages) if m.id != user_message.id
        ]

        # --- Stage 3: 用户已经点击了推荐选项 (Deep RAG) ---
        if selected_node_uuid:
            logger.info(f"[RAG Stage 3] Fetching deep context for UUID: {selected_node_uuid}")
            graph_context = graph_service.fetch_deep_context(selected_node_uuid)
            ai_structured_cards = []
            final_reply = "抱歉，我没有找到相关的图谱资料。"
            
            if graph_context:
                problem_name = graph_context.get("problem_name") or graph_context.get("名称") or "您关注的问题"
                if not graph_context or (not graph_context.get("treatments") and not graph_context.get("articles")):
                    final_reply = f"关于“{problem_name}”，我目前主要建议你关注校园心理中心的动态。你可以点击下方卡片查看基础应对策略："
                else:
                    final_reply = f"关于“{problem_name}”，我为你找到了一些可能有帮助的建议："
                
                # 每种类型只取前 1 个，其余引导至知识库查看详情
                # 1. 危机干预 (CRISIS)
                for plan in graph_context.get("emergency_plans", [])[:1]:
                    ai_structured_cards.append({
                        "type": "CRISIS", "title": plan.get("title", ""),
                        "content": plan.get("content", ""),
                        "extra_info": {"contacts": plan.get("contacts", "")}
                    })
                
                # 2. 应对技巧 (TREATMENT)
                for t in graph_context.get("treatments", [])[:1]:
                    ai_structured_cards.append({
                        "type": "TREATMENT", "title": t.get("name", ""),
                        "content": t.get("content") or t.get("method", ""),
                        "extra_info": {"method": t.get("method", "")}
                    })
                    
                # 3. 校园政策 (POLICY)
                for p in graph_context.get("campus_policies", [])[:1]:
                    ai_structured_cards.append({
                        "type": "POLICY", "title": p.get("name", ""),
                        "content": p.get("content", ""),
                        "extra_info": {"department": p.get("department", "")}
                    })
                    
                # 4. 科普文章 (ARTICLE)
                for a in graph_context.get("articles", [])[:1]:
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
                knowledge_base_uuid=selected_node_uuid,
                intent_type="QUERY_TREATMENT"
            )
            
            # 卡片发放完毕，清除当前槽位，开启新的对话周期
            cache.delete(f"chat_slots_{session_id}")
            
            return {
                "session_id": str(session.id),
                "reply": final_reply,
                "structured_cards": ai_structured_cards,
                "cards": ai_structured_cards, # 为了绝对兼容性，保留 cards 冗余
                "knowledge_base_uuid": selected_node_uuid,
                "stage": "FINAL"
            }

        # --- Stage 1 & 2: 动态追问与推荐 ---
        current_slots = self._get_session_slots(session_id)
        logger.info(f"Session {session_id} current slots: {current_slots}")
        
        # [NEW] 自适应提速：前置进行向量检索，为 Stage 1 提供候选建议
        search_query = f"{content} {current_slots.get('event', '')}"
        candidates = graph_service.find_candidates(search_query, top_k=5)
        
        # 1. 调用槽位感知的 LLM (传入候选建议)
        llm_res = llm_service.slot_aware_follow_up(content, current_slots, candidates=candidates, history=history_list)
        
        # 2. 处理危机检测 (Soft Detection)
        if llm_res.intent_type == "CRISIS_ALERT":
            logger.warning(f"Session {session_id} - LLM detected Crisis Alert!")
            cache.delete(f"chat_slots_{session_id}")
            ChatMessage.objects.create(
                session=session,
                role="ai",
                content=llm_res.empathy_reply,
                structured_cards=[],
                intent_type="CRISIS_ALERT"
            )
            return {
                "session_id": str(session.id),
                "reply": llm_res.empathy_reply,
                "cards": [],
                "intent": {"intent_type": "CRISIS_ALERT"}
            }

        # 3. 更新槽位状态
        if hasattr(llm_res, 'slots_collected') and llm_res.slots_collected:
            current_slots = self._update_session_slots(session_id, llm_res.slots_collected, current_slots)
        
        # 4. 判断是否完成收敛
        # 如果 LLM 已经给出了高质量选项 (由于混合模式开启)，或者槽位全满
        if llm_res.collection_status == "COMPLETED" or all(current_slots.values()):
            logger.info(f"Session {session_id} slots completed or fast-tracked.")
            
            # 如果 llm_res 已经包含选项（混合模式下产生的），则直接采用
            if llm_res.options:
                rec_res = llm_res
            else:
                from datetime import datetime
                current_month = f"{datetime.now().month}月"
                search_query = f"{content} {current_slots.get('event', '')} {current_slots.get('impact', '')}"
                
                # 尝试获取带有时空感知的深度上下文作为推荐依据
                top_candidate = candidates[0] if candidates else None
                if top_candidate:
                    deep_context = graph_service.fetch_deep_context(top_candidate['uuid'], current_month=current_month)
                    # 将深度上下文中的地点、事件等信息补充到候选列表中供 LLM 参考
                    if deep_context and deep_context.get('treatments'):
                        for t in deep_context['treatments']:
                            if t.get('location'):
                                candidates.append({
                                    "uuid": t.get('uuid'),
                                    "name": f"{t.get('name')} [建议地点: {t.get('location')}]",
                                    "description": t.get('content', '')
                                })
                
                rec_res = llm_service.get_recommendation_with_context(current_slots, candidates, history_list)

        # 3. 构造基础响应 (Base Response)
        # 如果已进入推荐阶段，使用 rec_res，否则使用 llm_res
        final_res = rec_res if (llm_res.collection_status == "COMPLETED" or all(current_slots.values())) else llm_res
        
        response_body = {
            "session_id": str(session.id),
            "reply": final_res.empathy_reply,
            "options": getattr(final_res, 'options', []),
            "stage": "RECOMMEND" if (llm_res.collection_status == "COMPLETED" or all(current_slots.values())) else "COLLECTING",
            "debug_slots": current_slots
        }
        
        # 4. 最终环节：风险感知拦截器 (Risk Perception Interceptor)
        # 无论在哪个 Stage，只要触发风险评估标记，则强制覆盖当前回复内容
        return self._inject_risk_intervention(user, session, response_body, final_res, shadow_intervention=shadow_intervention)

    def _inject_risk_intervention(self, user, session, response_body, final_res, shadow_intervention=None):
        """
        检查并注入风险干预。
        1. 首先处理“影子干预”（基于关键词的 Soft Detection）。
        2. 其次处理基于画像维度的“个性化风险干预”。
        """
        # --- 1. 处理影子干预 (关键词提示) ---
        if shadow_intervention:
            # 如果不需要拦截 (中低危)，将解析到的量表建议也注入其中
            if shadow_intervention.get("suggested_scale"):
                response_body["suggested_assessment"] = shadow_intervention["suggested_scale"]
                response_body["stage"] = "INTERVENTION"
                logger.info(f"Injected suggested_scale from shadow intervention: {response_body['suggested_assessment']['scale_id']}")

            # 将拦截到的干预卡片合并到响应中
            if "structured_cards" not in response_body:
                response_body["structured_cards"] = []
            response_body["structured_cards"].extend(shadow_intervention.get("structured_cards", []))
            logger.info(f"Injected {len(shadow_intervention['cards'])} shadow cards into response.")

        # 依据会话深度决定话术前缀
        session_msg_count = ChatMessage.objects.filter(session=session, role='user').count()
        is_new_session = session_msg_count <= 1

        DIMENSION_MAP = {
            "焦虑": {
                "scale_id": "scale_academic_stress_v2",
                "title": "学业压力与职业焦虑评估",
                "templates": {
                    "new": "看到你刚才提到的内容，我联想到你近期整体呈现出较明显的学业或前途焦虑感。这些压力可能正在暗中影响你，为了精准了解压力源，建议进行一次专项评估。",
                    "ongoing": "我注意到你最近多次提到关于“学业或前途”的焦虑感，这些压力可能正在影响你的状态。为了精准了解你的压力源，我建议你进行一次专项评估。"
                }
            },
            "抑郁": {
                "scale_id": "scale_mental_crisis_v2",
                "title": "情绪健康与风险综合筛查",
                "templates": {
                    "new": "在今天的对话中，我从你的叙述里感受到了些许沉重。结合近期的整体情况，这种低落感似乎已累积了一段时间。我想邀请你做一个深度的情绪筛查，看看我们能如何更好地支持你。",
                    "ongoing": "最近你的话语中流露出较重的低落感和无力感，这让我有些担心。我想邀请你做一个深度的情绪筛查，看看我们能如何更好地支持你。"
                }
            },
            "躯体化": {
                "scale_id": "scale_mental_crisis_v2",
                "title": "躯体不适与心理健康筛查",
                "templates": {
                    "new": "看到你刚才提到的这些身体不适（如胸闷、失眠等），这往往是心理压力的报警信号。结合近期的观察，建议你先进行这个综合心理状态评估。",
                    "ongoing": "你提到的这些身体不适往往是心理压力的报警信号。为了安全起见，建议你先进行这个综合心理状态评估。"
                }
            },
            "人际敏感": {
                "scale_id": "scale_interpersonal_v2",
                "title": "校园社交与人际质量评估",
                "templates": {
                    "new": "听起来你在人际关系中遇到了一些困扰。结合这类情绪的近期监测情况，建议你通过这个量表来梳理一下现状。",
                    "ongoing": "听起来你在校园社交或宿舍关系中遇到了一些困扰，这些不愉快可能会消耗你很多精力。建议你通过这个量表来梳理一下现状。"
                }
            }
        }

        dimensions = list(DIMENSION_MAP.keys())
        for dim in dimensions:
            trigger_key = f"assessment_trigger:{user.id}:{dim}"
            if cache.get(trigger_key):
                logger.info(f"Triggering Personalised Risk Intervention for User {user.id} on dimension {dim} (NewSession: {is_new_session})")
                
                config = DIMENSION_MAP.get(dim)
                reply_text = config["templates"]["new"] if is_new_session else config["templates"]["ongoing"]

                response_body["reply"] = reply_text
                response_body["options"] = [] 
                response_body["suggested_assessment"] = {
                    "scale_id": config["scale_id"],
                    "reason": f"监测到较强烈的“{dim}”倾向累积。",
                    "title": config["title"]
                }
                response_body["stage"] = "INTERVENTION" 

                ChatMessage.objects.create(
                    session=session,
                    role="ai",
                    content=response_body["reply"],
                    suggested_assessment=response_body["suggested_assessment"],
                    structured_cards=[],
                    intent_type="ASSESSMENT_TRIGGER"
                )
                
                cache.delete(trigger_key)
                
                # 同步重置隐式分值，进入“评估观察期”
                try:
                    from apps.services.profiling_service import profiling_service
                    profiling_service.reset_dimension_score(user.id, dim)
                except Exception as e:
                    logger.error(f"Failed to reset profiling score: {str(e)}")
                
                return response_body
        
        # 如果没有触发干预，则正常记录 AI 回复
        ChatMessage.objects.create(
            session=session, role="ai", content=response_body["reply"],
            structured_cards=response_body.get("structured_cards", []), 
            intent_type=getattr(final_res, 'intent_type', 'CHAT')
        )
        return response_body
    
    def generate_assessment_feedback(self, user, session_id, report):
        """
        [闭环逻辑] 当用户完成一次由聊天触发的测评后，AI 自动生成一条针对结果的反馈回复。
        """
        try:
            from django.apps import apps
            ChatMessage = apps.get_model('apps', 'ChatMessage')
            ChatSession = apps.get_model('apps', 'ChatSession')
            
            session = ChatSession.objects.get(id=session_id)
            score = report.get('total_score', 0)
            level = report.get('level', '未知')
            scale_name = report.get('scale_name', '心理测评')
            
            # 构造反馈文案
            if score > 30: # 假设 30 分以上为高风险
                feedback_text = f"我已经收到了你的《{scale_name}》报告。结果显示你的压力分值较高（{score}分，{level}），这确实是一个需要重视的信号。请不要独自承受，建议点击下方推荐的资源寻找专业支持，或者我们可以针对这个结果聊聊具体的应对方法。"
            else:
                feedback_text = f"看到你完成了《{scale_name}》！结果显示在当前评估中你的状态相对平稳（{score}分，{level}）。保持这样的状态很棒，如果以后有任何波动，记得随时来找我倾诉。"
            
            # 持久化 AI 反馈消息
            ChatMessage.objects.create(
                session=session,
                role="ai",
                content=feedback_text,
                intent_type="ASSESSMENT_FEEDBACK"
            )
            logger.info(f"Generated assessment feedback for User {user.id} in Session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error generating assessment feedback: {str(e)}")
            return False

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

import logging
from apps.repositories.neo4j_repo import neo4j_repo
from apps.services.llm_service import UserIntentAnalysis
from apps.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class GraphService:
    """
    负责将大模型的意图转化为图谱的精确查询，并进行业务规则处理。
    """
    
    def fetch_context_for_intent(self, intent: UserIntentAnalysis, user_input: str = "") -> dict:
        """
        根据 LLM 识别出的意图和问题，从图谱获取完整的问诊知识树。
        增加短路逻辑：如果是纯聊天或专门查政策，走专用分流通道以节省 IO 并提高准确率。
        """
        # 1. 纯日常聊天且无明确问题，直接短路（极大节省图数据库 IO）
        if intent.intent_type == "CHAT" and not intent.problem_name:
            logger.info("Intent is CHAT and no problem detected, short-circuiting graph retrieval.")
            return None
            
        # 2. 专门查询校园政策，走 Policy 检索链路
        if intent.intent_type == "QUERY_POLICY":
            # 优先用 LLM 提取的问题名称作关键词，如果没有则直接用原句去匹配
            search_keyword = intent.problem_name if intent.problem_name else user_input
            logger.info(f"Intent is QUERY_POLICY, searching keyword: {search_keyword}")
            if hasattr(neo4j_repo, 'find_policy_by_keyword'):
                res = neo4j_repo.find_policy_by_keyword(search_keyword)
                # 增强：如果全词匹配失败且有症状，尝试用症状作为关键词兜底
                if not res and intent.symptoms:
                    for sym in intent.symptoms:
                        logger.info(f"Policy full match failed, retrying with symptom: {sym}")
                        res = neo4j_repo.find_policy_by_keyword(sym)
                        if res: break
                return res
            return None

        # 3. 心理问题咨询或高危预警 (QUERY_TREATMENT, CRISIS_ALERT)
        if intent.problem_name:
            # 优先根据提取的明确心理问题名称去检索
            context = neo4j_repo.get_psychological_problem_graph(intent.problem_name)
            if context:
                return self._append_safety_info(context)

        # 4. 如果没有明确匹配到，尝试根据症状列表进行模糊反查
        if intent.symptoms:
            matched_problem = neo4j_repo.find_problem_by_symptoms(intent.symptoms)
            if matched_problem:
                logger.info(f"Fuzzy matched problem '{matched_problem}' by symptoms {intent.symptoms}")
                context = neo4j_repo.get_psychological_problem_graph(matched_problem)
                return self._append_safety_info(context)

        # 5. 最终兜底：如果明确是咨询意图但没中，用用户原句在图谱中搜素最接近的关键词
        if intent.intent_type in ["QUERY_TREATMENT", "CRISIS_ALERT"]:
            fuzzy_problem = neo4j_repo.find_problem_by_keyword(user_input)
            if fuzzy_problem:
                logger.info(f"Fuzzy matched problem '{fuzzy_problem}' by raw user input keyword.")
                context = neo4j_repo.get_psychological_problem_graph(fuzzy_problem)
                return self._append_safety_info(context)

        return None

    def find_candidates(self, user_input: str, top_k: int = 5) -> list:
        """
        利用向量检索寻找候选匹配节点。
        """
        embedding = embedding_service.get_embedding(user_input)
        if not embedding:
            return []
        raw_candidates = neo4j_repo.vector_search_candidates(embedding, top_k=top_k)
        
        # 归一化键名，方便 LLM 处理 (将中文键名 '.名称' 映射为 'name')
        normalized = []
        for c in raw_candidates:
            normalized.append({
                "uuid": c.get("uuid"),
                "name": c.get("名称"), # 关键：映射中文键名
                "description": c.get("描述", "")
            })
        return normalized

    def fetch_deep_context(self, uuid: str) -> dict:
        """
        根据 UUID 直接获取图谱深度背景，并补充 MySQL 中的风险等级与应急预案信息。
        """
        context = neo4j_repo.get_psychological_problem_graph(uuid=uuid)
        return self._append_safety_info(context)

    def _append_safety_info(self, context: dict) -> dict:
        """
        [Join Logic] 根据图谱中的 risk_level 字符串，从 MySQL 获取详细预案。
        """
        if not context or 'risk_level' not in context:
            return context
            
        risk_name = context.get('risk_level')
        from apps.models import RiskLevel, EmergencyPlan
        
        try:
            # 1. 查找风险定义
            rl = RiskLevel.objects.filter(name=risk_name).first()
            if rl:
                context['risk_details'] = {
                    "name": rl.name,
                    "description": rl.description,
                    "color": rl.color_code,
                    "priority": rl.priority
                }
                
                # 2. 如果是高危/极高危，附带预案
                if rl.priority >= 2:
                    plans = EmergencyPlan.objects.filter(risk_level=rl)
                    context['emergency_plans'] = [
                        {
                            "title": p.title,
                            "content": p.content,
                            "contacts": p.contacts
                        } for p in plans
                    ]
        except Exception as e:
            logger.error(f"Failed to append safety info: {str(e)}")
            
        return context

graph_service = GraphService()

import logging
from apps.repositories.neo4j_repo import neo4j_repo
from apps.services.llm_service import UserIntentAnalysis

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
        # 1. 纯日常聊天，直接短路（极大节省图数据库 IO）
        if intent.intent_type == "CHAT":
            logger.info("Intent is CHAT, short-circuiting graph retrieval.")
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
                return context

        # 4. 如果没有明确匹配到，尝试根据症状列表进行模糊反查
        if intent.symptoms:
            matched_problem = neo4j_repo.find_problem_by_symptoms(intent.symptoms)
            if matched_problem:
                logger.info(f"Fuzzy matched problem '{matched_problem}' by symptoms {intent.symptoms}")
                return neo4j_repo.get_psychological_problem_graph(matched_problem)

        return None

graph_service = GraphService()

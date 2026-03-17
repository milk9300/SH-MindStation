import logging
from apps.repositories.neo4j_repo import neo4j_repo
from apps.services.llm_service import UserIntentAnalysis

logger = logging.getLogger(__name__)

class GraphService:
    """
    负责将大模型的意图转化为图谱的精确查询，并进行业务规则处理。
    """
    
    def fetch_context_for_intent(self, intent: UserIntentAnalysis) -> dict:
        """
        根据 LLM 识别出的意图和问题，从图谱获取完整的问诊知识树。
        """
        if intent.problem_name:
            # 1. 优先根据提取的明确心理问题名称去检索
            context = neo4j_repo.get_psychological_problem_graph(intent.problem_name)
            if context:
                return context

        # 2. 如果没有明确匹配到，尝试根据症状列表进行反查
        if intent.symptoms:
            matched_problem = neo4j_repo.find_problem_by_symptoms(intent.symptoms)
            if matched_problem:
                logger.info(f"Fuzzy matched problem '{matched_problem}' by symptoms {intent.symptoms}")
                return neo4j_repo.get_psychological_problem_graph(matched_problem)

        return None

graph_service = GraphService()

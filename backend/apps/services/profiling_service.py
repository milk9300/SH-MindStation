import logging
import uuid
from django.db import transaction
from django.core.cache import cache
from apps.repositories.neo4j_repo import neo4j_repo
from apps.models import AuditLog, User

logger = logging.getLogger(__name__)

class ProfilingService:
    def record_symptoms(self, user_id, symptoms, session_id=None):
        if not symptoms:
            return
        
        try:
            # 1. 在 Neo4j 中查找症状归属的维度
            results = self._fetch_dimensions_for_symptoms(symptoms)
            
            # 2. 更新 Redis 中的隐式分值 (按用户+维度聚合)
            direct_impact_dims = ["焦虑", "抑郁"] # 对这些维度，如果用户提及则加 3 分
            for dim_name, weight in results.items():
                cache_key = f"implicit_profile:{user_id}:{dim_name}"
                current_val = cache.get(cache_key, 0)
                
                # 策略：如果属于高权重维度，则权重放大到 3
                final_weight = weight * 3 if dim_name in direct_impact_dims else weight
                
                cache.set(cache_key, current_val + final_weight, timeout=86400 * 7) # 有效期一周
                
                logger.info(f"Updated implicit score for user {user_id}, dimension {dim_name}: {current_val + final_weight} (added {final_weight})")
            
            # 3. 记录对齐日志 (MySQL)
            self._log_mapping_event(user_id, session_id, symptoms, results)
            
        except Exception as e:
            logger.error(f"Error in recording symptoms: {str(e)}")

    def _fetch_dimensions_for_symptoms(self, symptoms):
        query = '''
            UNWIND $symptoms AS sym_name
            MATCH (s:症状) WHERE s.名称 = sym_name
            MATCH (s)-[:属于]->(d:Dimension)
            RETURN d.name AS dim_name, count(s) AS count
        '''
        results = {}
        try:
            with neo4j_repo.driver.session() as session:
                res = session.run(query, symptoms=symptoms)
                for record in res:
                    results[record["dim_name"]] = record["count"]
        except Exception as e:
            logger.error(f"Neo4j dim mapping error: {str(e)}")
        return results

    def _log_mapping_event(self, user_id, session_id, symptoms, results):
        try:
            # 确保 MySQL 与 Neo4j UUID 在日志中对齐
            detail = {
                "session_id": session_id,
                "input_symptoms": symptoms,
                "mapped_dimensions": results,
                "msg": "Implicit profiling update"
            }
            user = User.objects.get(id=user_id)
            AuditLog.objects.create(
                admin=user,
                action_module="PROFILING",
                action_type="IMPLICIT_SCORE",
                target_detail=str(detail)
            )
        except Exception as e:
            logger.error(f"Failed to log profiling event: {str(e)}")

    def get_user_dashboard_data(self, user_id):
        """
        获取用于看板展示的结构化数据，包括雷达图、意图分析和动态建议。
        """
        import random
        
        # 1. 雷达图维度
        dimensions = [
            {"name": "焦虑", "base": 18},
            {"name": "抑郁", "base": 15},
            {"name": "压力", "base": 22},
            {"name": "应对能力", "base": 65},
            {"name": "心理韧性", "base": 60},
            {"name": "幸福感", "base": 70}
        ]
        
        scores = []
        for d in dimensions:
            # 尝试获取真实数据，如果没有则使用 base + 随机扰动
            val = cache.get(f"implicit_profile:{user_id}:{d['name']}")
            if val is None:
                # 模拟一个相对健康的初始底色，并带有 ±5 的随机扰动
                val = d["base"] + random.randint(-5, 5)
            
            scores.append(min(max(int(val), 5), 100))
            
        # 2. 意图分析 (逻辑增强：尝试从用户最近的聊天中提取高频标签)
        # 这里先根据分值异常情况动态生成，后续可结合 LLM 统计
        intents = []
        if scores[0] > 40: intents.append("近期关注：焦虑情绪持续时间较长")
        if scores[2] > 40: intents.append("核心压力：学业或就业竞争压力")
        
        # 默认兜底意图 (如果没数据)
        if not intents:
            intents = [
                "近期状态：情绪底色相对平稳",
                "潜在需求：倾向于通过倾诉缓解压力",
                "积极因素：具备较好的自我调节潜力"
            ]
        
        # 3. 智能建议 (基于维度的优先级排序生成)
        recommendations = []
        # 找出分值最高的消极维度或分值最低的积极维度
        stress_score = scores[2]
        resilience_score = scores[4]
        
        if stress_score > 30:
            recommendations.append("识别到压力脉冲，建议尝试“肌肉放松法”")
        if resilience_score < 50:
            recommendations.append("心理韧性处于成长期，建议阅读《逆境生长》导读")
        
        # 兜底建议
        if len(recommendations) < 3:
            recommendations.extend([
                "每天记录一件“确定的幸事”，提升幸福感",
                "睡前尝试进行 10 分钟的呼吸冥想",
                "如果感到困惑，随时点击下方按钮与我聊聊"
            ])

        return {
            "radar_data": {
                "categories": [d["name"] for d in dimensions],
                "series": [{"name": "当前状态", "data": scores}]
            },
            "intents": intents[:3],
            "recommendations": recommendations[:3],
            "overall_score": sum(scores) // 6
        }

    def get_user_risk_profile(self, user_id):
        dimensions = ["焦虑", "抑郁", "躯体化", "人际敏感", "压力"]
        profile = {}
        for dim in dimensions:
            profile[dim] = cache.get(f"implicit_profile:{user_id}:{dim}", 0)
        return profile

    def reset_dimension_score(self, user_id, dimension):
        """
        重置特定维度的隐式分值。
        通常在触发测评建议或完成测评后调用，以防止重复触发。
        """
        cache_key = f"implicit_profile:{user_id}:{dimension}"
        cache.delete(cache_key)
        logger.info(f"Reset implicit score for user {user_id}, dimension {dimension}")

profiling_service = ProfilingService()

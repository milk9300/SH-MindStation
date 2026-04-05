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

    def get_user_risk_profile(self, user_id):
        dimensions = ["焦虑", "抑郁", "躯体化", "人际敏感"]
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

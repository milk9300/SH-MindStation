import uuid
import logging
import json
from django.core.cache import cache
from apps.models import AssessmentScale, AssessmentQuestion, AssessmentRecord, User
from apps.repositories.neo4j_repo import neo4j_repo

logger = logging.getLogger(__name__)

class AssessmentService:
    def start_session(self, user_id, scale_id):
        session_id = str(uuid.uuid4())
        scale = AssessmentScale.objects.filter(id=scale_id).first()
        if not scale:
            raise Exception("Scale not found")
        
        # 获取第一题
        first_q = scale.questions.order_by('sort_order').first()
        
        state = {
            "scale_id": scale_id,
            "scale_name": scale.name,
            "user_id": user_id,
            "current_q_id": first_q.id if first_q else None,
            "answers": [],
            "dimension_scores": {},
            "is_finished": False
        }
        
        cache.set(f"assessment_session:{session_id}", state, timeout=3600)
        return session_id, first_q

    def submit_answer(self, session_id, q_id, option_label, score):
        state = cache.get(f"assessment_session:{session_id}")
        if not state:
            raise Exception("Session expired or not found")
        
        question = AssessmentQuestion.objects.get(id=q_id)
        dimension = question.dimension or "通用"
        
        # 1. 更新维度得分
        state["dimension_scores"][dimension] = state["dimension_scores"].get(dimension, 0) + score
        state["answers"].append({
            "q_id": q_id,
            "content": question.content,
            "a_label": option_label,
            "score": score,
            "dimension": dimension
        })
        
        # 2. 实时风险拦截: 如果触发了危机相关维度的得分，立即记录日志
        if dimension in ["高危行为", "危机意念", "终极行动"] and score > 0:
            logger.warning(f"CRITICAL: User {state.get('user_id')} triggered crisis dimension {dimension} in assessment!")
            try:
                from apps.models import CrisisAlertLog, ChatMessage
                # 尝试找到最近的一条针对该用户的消息作为关联（由于测评是异步的，这里做尽力而为的关联）
                user = User.objects.get(id=state.get('user_id'))
                last_msg = ChatMessage.objects.filter(session__user=user).order_by('-created_at').first()
                if last_msg:
                    CrisisAlertLog.objects.get_or_create(
                        message=last_msg,
                        defaults={
                            "user": user,
                            "risk_level": "红色" if dimension in ["危机意念", "终极行动"] else "高危",
                            "trigger_symptom": f"量表命中: {dimension} ({question.content[:20]})",
                            "status": "pending"
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to create CrisisAlertLog during assessment: {str(e)}")

        # 3. CAT 自适应逻辑: 检查当前维度风险
        
        # 3. 获取下一题
        next_q = self._get_next_question(state, question, should_skip_dimension)
        
        if not next_q:
            state["is_finished"] = True
            
        cache.set(f"assessment_session:{session_id}", state, timeout=3600)
        return next_q, state["is_finished"]

    def _check_cat_skip(self, state, dimension):
        # 模拟逻辑：最近三道同维度的题得分都为 1
        dim_answers = [a for a in state["answers"] if a["dimension"] == dimension]
        if len(dim_answers) >= 3:
            recent_scores = [a["score"] for a in dim_answers[-3:]]
            if all(s == 1 for s in recent_scores):
                logger.info(f"CAT: Skipping dimension {dimension} for session {state.get('scale_id')}")
                return True
        return False

    def _get_next_question(self, state, current_q, skip_current_dim=False):
        scale = AssessmentScale.objects.get(id=state["scale_id"])
        
        query = scale.questions.filter(sort_order__gt=current_q.sort_order)
        if skip_current_dim:
            query = query.exclude(dimension=current_q.dimension)
            
        return query.order_by('sort_order').first()

    def generate_final_report(self, user_id, session_id):
        state = cache.get(f"assessment_session:{session_id}")
        if not state or not state["is_finished"]:
            return None
        
        user = User.objects.get(id=user_id)
        total_score = sum(a["score"] for a in state["answers"])
        
        # 匹配等级 (简化版)
        level = "正常"
        scale = AssessmentScale.objects.get(id=state["scale_id"])
        for rule in scale.scoring_rules:
            if total_score >= rule.get("min", 0) and total_score <= rule.get("max", 999):
                level = rule.get("result", "正常")
                break
        
        # RAG 召回校园干预资源 (从 Neo4j 查找)
        recommendations = {}
        for dim, score in state["dimension_scores"].items():
            if score > 3: # 假设单维度风险阈值
                recommendations[dim] = self._fetch_graph_resources(dim)

        # 持久化到 MySQL (改为同步以获取 ID 供前端跳转)
        record = AssessmentRecord.objects.create(
            user=user,
            scale_name=state["scale_name"],
            total_score=total_score,
            result_level=level,
            report_json=state["answers"],
            dimension_scores=state["dimension_scores"]
        )
        logger.info(f"Sync: Saved assessment record {record.id} for user {user_id}")
        
        # 4. 获取历史趋势 (最新 10 条)
        history = self._get_user_history(user_id, state["scale_name"])
        # 将本次结果也加入趋势图末尾进行对比
        history.append({
            "date": "本次",
            "score": total_score
        })

        return {
            "record_id": record.id,
            "scale_name": state["scale_name"],
            "total_score": total_score,
            "level": level,
            "dimension_scores": state["dimension_scores"],
            "recommendations": recommendations,
            "history": history,
            "msg": "Report generated, history included."
        }

    def _get_user_history(self, user_id, scale_name):
        records = AssessmentRecord.objects.filter(
            user_id=user_id,
            scale_name=scale_name
        ).order_by('-created_at')[:10]
        
        history_list = []
        # 按时间正序排列（图表从左往右）
        for r in reversed(records):
            history_list.append({
                "date": r.created_at.strftime("%m-%d"),
                "score": r.total_score
            })
        return history_list

    def _fetch_graph_resources(self, dimension):
        query = '''
            MATCH (d:Dimension {name: $name})-[:关联策略]->(s:应对技巧)-[:建议物理场所]->(loc:校园地点)
            RETURN s.名称 AS strategy, loc.名称 AS location, loc.负责人 AS contact
        '''
        res_list = []
        try:
            with neo4j_repo.driver.session() as session:
                res = session.run(query, name=dimension)
                for record in res:
                    res_list.append({
                        "name": record["strategy"],
                        "location": record["location"],
                        "contact": record["contact"]
                    })
        except Exception as e:
            logger.error(f"Neo4j rec recall error: {str(e)}")
        return res_list

assessment_service = AssessmentService()

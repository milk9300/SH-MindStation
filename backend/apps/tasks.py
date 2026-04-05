import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 显式加载环境变量 (确保 Worker 进程能获取到 LLM_API_KEY 等)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# 2. Windows + Eventlet DNS 兼容性“终极”补丁 (仅在 Celery Worker 进程中激活)
import sys
if 'celery' in sys.argv[0] or (len(sys.argv) > 1 and sys.argv[1] == 'worker'):
    try:
        import dns.resolver
        import dns.name
        # 强行劫持 read_registry 方法，阻止其读取 Windows 损坏的注册表
        def mock_read_registry(self, timeout=None):
            self.nameservers = ['8.8.8.8', '8.8.4.4', '114.114.114.114']
            self.domain = dns.name.Name(['local'])
            self.search = []
        
        # 覆盖原生方法
        dns.resolver.Resolver.read_registry = mock_read_registry
        
        # 强制重置当前解析器
        resolver = dns.resolver.get_default_resolver()
        resolver.nameservers = ['8.8.8.8', '8.8.4.4', '114.114.114.114']
        print("[SH MindStation] DNS Registry Patcher Activated: Registry reading disabled.")
    except Exception as e:
        print(f"[SH MindStation] DNS Patch Failed: {str(e)}")

from celery import shared_task
from django.db import transaction
from apps.models import AssessmentRecord, User

logger = logging.getLogger(__name__)

@shared_task(name="apps.tasks.async_save_assessment")
def async_save_assessment(user_id, scale_name, total_score, level, report_json, dimension_scores):
    """
    异步将测评结果持久化到 MySQL。
    在高并发场景下，此任务由 Celery 消费，减轻数据库主库压力。
    """
    try:
        with transaction.atomic():
            user = User.objects.get(id=user_id)
            record = AssessmentRecord.objects.create(
                user=user,
                scale_name=scale_name,
                total_score=total_score,
                result_level=level,
                report_json=report_json,
                dimension_scores=dimension_scores
            )
            logger.info(f"Async: Saved assessment record {record.id} for user {user_id}")
            return record.id
    except Exception as e:
        logger.error(f"Async save assessment error: {str(e)}")
        return None

@shared_task(name="apps.tasks.generate_mental_report")
def generate_mental_report(record_id):
    """
    后期扩展：生成 PDF 报告或深入的数据分析。
    """
    pass

@shared_task(name="apps.tasks.async_profile_user")
def async_profile_user(user_id, session_id, content, message_id=None):
    """
    异步分析用户聊天内容中的症状并记录到隐式画像。
    [新增] 基于 message_id 的幂等性校验，防止网络重试导致的分值重复累加。
    """
    try:
        from apps.services.llm_service import llm_service
        from apps.services.profiling_service import profiling_service
        from django.core.cache import cache
        
        # 0. 幂等性校验
        if message_id:
            lock_key = f"profile_lock:{message_id}"
            if cache.get(lock_key):
                logger.info(f"Skip profiling for message {message_id} (already processed)")
                return
            cache.set(lock_key, True, timeout=600) # 10分钟内不再重复处理同一条消息
        
        # 1. 调用 LLM 提取症状 (Intent Analysis 兼顾症状提取)
        analysis = llm_service.analyze_intent(content)
        if analysis and analysis.symptoms:
            # 2. 记录到隐式画像 (Neo4j -> Redis)
            profiling_service.record_symptoms(user_id, analysis.symptoms, session_id)
            logger.info(f"Async Profile: Recorded symptoms {analysis.symptoms} for user {user_id}")
            
            # 3. [触发逻辑] 监控阈值，为后续可能的测评引导做准备
            profile = profiling_service.get_user_risk_profile(user_id)
            for dim, score in profile.items():
                if score >= 5: # 假设 5 分为阶段性风险预警
                    cache_key = f"assessment_trigger:{user_id}:{dim}"
                    if not cache.get(cache_key):
                        cache.set(cache_key, True, timeout=3600)
                        logger.info(f"Threshold reached for {dim}, assessment trigger set.")
                        
    except Exception as e:
        logger.error(f"Async profile user error: {str(e)}")

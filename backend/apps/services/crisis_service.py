import re
import time
import logging
from typing import Optional, Dict, Any
from apps.models import CrisisKeyword

logger = logging.getLogger(__name__)

class CrisisInterceptor:
    """
    毫秒级硬性拦截器：在进入 LLM 逻辑前，预先扫描用户输入的情绪极值或自残自杀意向。
    支持从数据库动态加载关键词。
    """
    
    def __init__(self):
        self._cached_regex = None
        self._last_refresh = 0
        self._refresh_interval = 300  # 5分钟刷新一次缓存
        
        # 兜底关键词（防止数据库为空时失效）
        self.DEFAULT_PATTERNS = [
            r"不想活了", r"想死", r"离开这个世界", r"自杀", r"跳楼", r"上吊", r"割腕",
            r"吃安眠药", r"吞药", r"绝笔", r"遗书"
        ]

    def _get_regex(self):
        """获取或刷新正则缓存"""
        now = time.time()
        if self._cached_regex and (now - self._last_refresh < self._refresh_interval):
            return self._cached_regex
            
        try:
            # 获取所有启用的“极高危”关键词
            db_keywords = list(CrisisKeyword.objects.filter(
                is_active=True, 
                level='critical'
            ).values_list('word', flat=True))
            
            # 合并：数据库关键词 + 兜底关键词，并去重
            patterns = list(set(db_keywords + self.DEFAULT_PATTERNS))
            
            # 性能优化：预编译
            self._cached_regex = re.compile("|".join(patterns), re.IGNORECASE)
            self._last_refresh = now
            logger.info(f"[CrisisInterceptor] Refreshed {len(patterns)} keywords (DB={len(db_keywords)}).")
        except Exception as e:
            logger.error(f"[CrisisInterceptor] Failed to refresh keywords: {str(e)}")
            if not self._cached_regex:
                self._cached_regex = re.compile("|".join(self.DEFAULT_PATTERNS), re.IGNORECASE)
        
        return self._cached_regex

    def fast_check(self, content: str) -> Optional[Dict[str, Any]]:
        """
        快速扫描。如果命中，直接从 MySQL 获取预设的紧急干预方案。
        """
        if not content:
            return None
            
        regex = self._get_regex()
        if regex.search(content):
            logger.warning(f"[HARD_CRISIS] Detected high-risk intent in input: {content[:100]}")
            
            # 从 MySQL 中获取极高危预警配置
            from apps.models import RiskLevel, EmergencyPlan
            
            try:
                # 1. 查找极高危风险定义
                critical_rl = RiskLevel.objects.filter(name__icontains='极高危').first()
                if not critical_rl:
                    # 兜底：获取优先级最高的
                    critical_rl = RiskLevel.objects.order_by('-priority').first()
                
                # 2. 获取预案
                plans = EmergencyPlan.objects.filter(risk_level=critical_rl)
                
                # 3. 构造结构化卡片
                cards = []
                for plan in plans:
                    cards.append({
                        "type": "CRISIS",
                        "title": f"🔴 {plan.title}",
                        "content": plan.content,
                        "extra_info": {
                            "level": critical_rl.name, 
                            "contacts": plan.contacts,
                            "domain": plan.domain
                        }
                    })
                
                # 如果没有配置预案，使用最后的硬性兜底
                if not cards:
                    cards = [{
                        "type": "CRISIS",
                        "title": "🔴 紧急救援资源",
                        "content": "请立刻联系校园中心或拨打 110/120。",
                        "extra_info": {"level": "极高危"}
                    }]

                return {
                    "is_crisis": True,
                    "reply": "同学，我听到了你言语中的痛苦，请立刻给自己一个停顿的机会，寻求专业力量的帮助，我们一直都在。",
                    "structured_cards": cards
                }
            except Exception as e:
                logger.error(f"[CrisisInterceptor] DB lookup failed during crisis: {str(e)}")
                # 极简兜底
                return {
                    "is_crisis": True,
                    "reply": "检测到高危提示，建议寻求帮助。",
                    "structured_cards": [{"type": "CRISIS", "title": "紧急救援", "content": "请拨打 110。"}]
                }
        return None

crisis_interceptor = CrisisInterceptor()

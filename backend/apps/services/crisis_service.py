import re
import time
import logging
from typing import Optional, Dict, Any
from apps.models import CrisisKeyword

logger = logging.getLogger(__name__)

class CrisisInterceptor:
    """
    分级安全拦截器：支持从数据库动态加载不同等级的关键词，并匹配最高风险等级的预案。
    """
    
    def __init__(self):
        self._cached_rules = None # 存储格式 {priority: {"regex": re.Pattern, "level_obj": RiskLevel}}
        self._last_refresh = 0
        self._refresh_interval = 300  # 5分钟刷新
        
        # 兜底行为：极高危识别
        self.HARD_DEFAULT_PATTERNS = [
            r"不想活了", r"想死", r"离开这个世界", r"自杀", r"跳楼", r"上吊", r"割腕",
            r"吃安眠药", r"吞药", r"绝笔", r"遗书"
        ]

    def _refresh_if_needed(self):
        """刷新策略：按优先级排序关键词"""
        now = time.time()
        if self._cached_rules and (now - self._last_refresh < self._refresh_interval):
            return
            
        try:
            from apps.models import RiskLevel, CrisisKeyword
            rules = []
            
            # 1. 获取所有存在的风险等级，按优先级从高到低排序 (数值越大越优先)
            levels = RiskLevel.objects.all().order_by('-priority')
            
            for lv in levels:
                # 获取该等级下所有启用的关键词
                words = list(CrisisKeyword.objects.filter(level=lv, is_active=True).values_list('word', flat=True))
                
                # 如果是“极高危”类等级且数据库为空，注入兜底词
                if not words and ('极高危' in lv.name or '危机' in lv.name):
                    words = self.HARD_DEFAULT_PATTERNS
                
                if words:
                    # 预编译正则，提高匹配速度
                    pattern = re.compile("|".join(words), re.IGNORECASE)
                    rules.append({
                        "priority": lv.priority,
                        "level_obj": lv,
                        "regex": pattern
                    })
            
            self._cached_rules = rules
            self._last_refresh = now
            logger.info(f"[CrisisInterceptor] Refreshed security rules. Levels loaded: {len(rules)}.")
        except Exception as e:
            logger.error(f"[CrisisInterceptor] Critical failure refreshing rules: {str(e)}")
            # 极度失败下的暴力兜底：创建一个虚拟的极高危规则
            if not self._cached_rules:
                self._cached_rules = [{
                    "priority": 999,
                    "level_obj": None, 
                    "regex": re.compile("|".join(self.HARD_DEFAULT_PATTERNS), re.IGNORECASE)
                }]

    def fast_check(self, content: str) -> Optional[Dict[str, Any]]:
        """
        分级扫描：从最高优先级的规则开始匹配。
        一旦命中，返回该等级对应的预案信息。
        """
        if not content:
            return None
            
        self._refresh_if_needed()
        
        for rule in self._cached_rules:
            if rule["regex"].search(content):
                level_obj = rule["level_obj"]
                level_name = level_obj.name if level_obj else "极高危"
                logger.warning(f"[SAFETY_HIT] Detected {level_name} in input: {content[:50]}...")
                
                # 获取预案
                from apps.models import EmergencyPlan
                cards = []
                suggested_scale = None
                
                if level_obj:
                    # 我们不仅获取 cards，还尝试提取关联的量表 ID (中危首选)
                    plans = EmergencyPlan.objects.filter(risk_level=level_obj)
                    for plan in plans:
                        # 核心逻辑：如果预案有关联量表，且是中低危，则优先设为推荐量表
                        if plan.scale_id and not suggested_scale:
                            suggested_scale = {
                                "scale_id": plan.scale_id,
                                "title": plan.title,
                                "reason": f"监测到涉及{plan.domain or '心理'}领域的敏感话题。"
                            }

                        cards.append({
                            "type": "CRISIS",
                            "title": plan.title,
                            "content": plan.content,
                            "action_type": plan.action_type,
                            "scale_id": plan.scale_id,
                            "button_text": plan.button_text,
                            "extra_info": {
                                "level": level_name,
                                "color": level_obj.color_code,
                                "contacts": plan.contacts,
                                "domain": plan.domain
                            }
                        })
                
                # 判定响应策略：如果等级包含“极高危”，则标记需要拦截
                should_interrupt = '极高危' in level_name or (level_obj and level_obj.priority >= 90)

                return {
                    "is_crisis": True,
                    "hit_level": level_name,
                    "priority": rule["priority"],
                    "should_interrupt": should_interrupt,
                    "reply": self._get_empathy_reply(level_name),
                    "structured_cards": cards,
                    "suggested_scale": suggested_scale # 返回可能的量表建议
                }
        
        return None

    def _get_empathy_reply(self, level_name: str) -> str:
        if '极高危' in level_name:
            return "同学，我听到了你言语中的痛苦，请立刻给自己一个停顿的机会，寻求专业力量的帮助，我们一直都在。"
        elif '高危' in level_name:
            return "我察觉到你现在的心情非常沉重，这些压力可能让你感到透不过气。除了和我聊聊，下面的这些专业支持或许能给你更直接的帮助。"
        return "感谢你的信任与分享。我注意到你提到的内容涉及一些敏感领域，为了你的心理健康，我为你准备了一些参考资源。"

crisis_interceptor = CrisisInterceptor()

crisis_interceptor = CrisisInterceptor()

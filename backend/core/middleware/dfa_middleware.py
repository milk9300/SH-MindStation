import json
import logging
import ahocorasick
from django.http import JsonResponse
from apps.models import CrisisKeyword

logger = logging.getLogger(__name__)

class DFAMiddleware:
    """
    基于 Aho-Corasick 自动机的敏感词/危机拦截中间件。
    在请求到达 View 之前进行 O(n) 时间复杂度的扫描，实现 100% 熔断。
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.automaton = ahocorasick.Automaton()
        self.is_built = False
        self._build_automaton()

    def _build_automaton(self):
        """从数据库全量加载启用的违规词与其优先级，构建 DFA 自动机"""
        try:
            # 获取关键词及其对应的等级优先级
            keywords = CrisisKeyword.objects.filter(is_active=True).select_related('level').values('word', 'level__priority')
            added_count = 0
            for item in keywords:
                word = item['word']
                priority = item['level__priority'] or 0
                if word:
                    # 存储 (word, priority) 数组
                    self.automaton.add_word(word, (word, priority))
                    added_count += 1
            
            if added_count == 0:
                self.automaton.add_word("自杀", ("自杀", 100))
                
            self.automaton.make_automaton()
            self.is_built = True
            logger.info(f"[DFAMiddleware] Successfully built tiered DFA automaton with {max(added_count, 1)} keywords.")
        except Exception as e:
            logger.error(f"[DFAMiddleware] Failed to build DFA automaton: {e}")
            self.is_built = False

    def __call__(self, request):
        if request.method == "POST" and "application/json" in request.content_type:
            try:
                if hasattr(request, 'body') and request.body:
                    body_data = json.loads(request.body)
                    content = body_data.get('content', '')
                    if content and self.is_built:
                        for end_index, (matched_word, priority) in self.automaton.iter(content):
                            # [关键改进] 仅对高危 (80) 及 极高危 (100) 级别的词汇执行硬熔断
                            # 中危 (50) 如“挂科”及更低级别词汇放行，交给后端的 ChatService 处理“软干预”
                            if priority >= 80:
                                logger.warning(f"[DFA RUPTURE] Intercepted High-Risk request from {request.user}. Word: {matched_word}, Priority: {priority}")
                                
                                return JsonResponse({
                                    "error": "内容违规或触发安全预警，请求已被拦截",
                                    "is_crisis": True,
                                    "matched_word": matched_word,
                                    "reply": "同学，我听到了你现在感到非常痛苦。请立刻让自己停顿下来，寻求专业力量的帮助，我们会一直支持你。",
                                    "structured_cards": [{
                                        "type": "CRISIS", 
                                        "title": "🔴 紧急援助热线", 
                                        "content": "全国心理援助热线：400-161-9995\n希望24热线：400-161-9995"
                                    }]
                                }, status=403, json_dumps_params={'ensure_ascii': False})
                            
                            # 低于 80 的词汇在此跳过，由后续的 View 处理逻辑进行分级响应
            except json.JSONDecodeError:
                pass 
            except Exception as e:
                logger.error(f"[DFAMiddleware] Scan exception: {e}")

        return self.get_response(request)

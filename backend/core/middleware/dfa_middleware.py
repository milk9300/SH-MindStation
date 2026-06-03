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

    def _resolve_user_from_token(self, request):
        """
        手动从 Authorization 请求头解析 DRF Token，获取关联用户。
        原因：DRF TokenAuthentication 在 View 层执行，中间件层 request.user 始终是 AnonymousUser。
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return None
        
        # 兼容 "Token xxx" 和 "Bearer xxx" 两种格式
        parts = auth_header.split()
        if len(parts) != 2:
            return None
        
        token_key = parts[1]
        
        try:
            from rest_framework.authtoken.models import Token
            token = Token.objects.select_related('user').get(key=token_key)
            return token.user
        except Exception:
            return None

    def _record_crisis_alert(self, user, matched_word, priority, content):
        """
        将 DFA 硬熔断事件持久化到 CrisisAlertLog，确保最高危拦截也能被后台管理平台追踪。
        注意：此处是中间件层，尚无 ChatMessage 记录，因此 message 字段设为 None。
        """
        try:
            from apps.models import CrisisAlertLog

            # 映射优先级到可读等级名称
            level_label = "极高危" if priority >= 100 else "高危"

            CrisisAlertLog.objects.create(
                user=user,
                message=None,       # 中间件层直接拦截，无对应 ChatMessage
                risk_level=level_label,
                trigger_symptom=f"[DFA熔断] 命中关键词「{matched_word}」，输入: {content[:30]}...",
                status=CrisisAlertLog.StatusChoices.PENDING
            )
            logger.info(f"[DFAMiddleware] CrisisAlertLog created for user {user.id} ({user.username}) | word={matched_word}")
        except Exception as e:
            # 审计写入失败不应阻塞熔断响应，降级为日志告警
            logger.error(f"[DFAMiddleware] Failed to persist CrisisAlertLog: {e}")

    def __call__(self, request):
        if request.method == "POST" and "application/json" in request.content_type:
            try:
                if hasattr(request, 'body') and request.body:
                    body_data = json.loads(request.body)
                    content = body_data.get('content', '')
                    if content and self.is_built:
                        for end_index, (matched_word, priority) in self.automaton.iter(content):
                            # [关键改进] 仅对高危 (80) 及 极高危 (100) 级别的词汇执行硬熔断
                            # 中危 (50) 如"挂科"及更低级别词汇放行，交给后端的 ChatService 处理"软干预"
                            if priority >= 80:
                                logger.warning(f"[DFA RUPTURE] Intercepted High-Risk request. Word: {matched_word}, Priority: {priority}")
                                
                                # [关键修复] 手动从 Token 解析用户，写入 CrisisAlertLog
                                # DRF 认证在 View 层，中间件层 request.user 是 AnonymousUser
                                resolved_user = self._resolve_user_from_token(request)
                                if resolved_user:
                                    self._record_crisis_alert(resolved_user, matched_word, priority, content)
                                else:
                                    logger.warning(f"[DFAMiddleware] Cannot resolve user from token, alert log skipped. Content: {content[:20]}...")
                                
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

import requests
import logging
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate

logger = logging.getLogger(__name__)
from rest_framework.authtoken.models import Token
from django.utils import timezone
from apps.models import (
    User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, 
    UserFavorite, AssessmentRecord, AuditLog, Article, AssessmentScale, 
    AssessmentQuestion, CrisisKeyword, RiskLevel, EmergencyPlan, GuidanceQuestion,
    ArticleComment
)
from apps.api.serializers import (
    UserSerializer, UserDetailedSerializer, ChatSessionSerializer, ChatSessionListSerializer,
    ChatMessageSerializer, CrisisAlertLogSerializer, UserMoodLogSerializer, UserFavoriteSerializer, 
    AuditLogSerializer, ArticleSerializer, AssessmentScaleSerializer, AssessmentScaleListSerializer,
    AssessmentQuestionSerializer, AssessmentRecordSerializer, CrisisKeywordSerializer,
    RiskLevelSerializer, EmergencyPlanSerializer, GuidanceQuestionSerializer,
    ArticleCommentSerializer
)

class RiskLevelViewSet(viewsets.ModelViewSet):
    """
    风险等级设置 (仅限管理员/高级别)
    """
    queryset = RiskLevel.objects.all().order_by('priority')
    serializer_class = RiskLevelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        audit_service.log_action(
            self.request.user, 'SAFETY', 'CREATE',
            f"定义了风险等级: {instance.name} (权重={instance.priority})",
            get_client_ip(self.request)
        )

class EmergencyPlanViewSet(viewsets.ModelViewSet):
    """
    预警应对方案设置 (仅限管理员/高级别)
    """
    queryset = EmergencyPlan.objects.all().select_related('risk_level')
    serializer_class = EmergencyPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        audit_service.log_action(
            self.request.user, 'SAFETY', 'CREATE',
            f"新增了处理预案: {instance.title} (关联等级={instance.risk_level.name if instance.risk_level else 'N/A'})",
            get_client_ip(self.request)
        )

class CrisisKeywordViewSet(viewsets.ModelViewSet):
    """
    违规词/敏感词管理 (仅限管理员)
    """
    queryset = CrisisKeyword.objects.all().select_related('level')
    serializer_class = CrisisKeywordSerializer
    permission_classes = [permissions.IsAuthenticated] # 实际生产中应加 IsAdminUser

    def perform_create(self, serializer):
        instance = serializer.save()
        audit_service.log_action(
            self.request.user, 'SAFETY', 'CREATE',
            f"新增了违规词: {instance.word} (级别={instance.level.name if instance.level else 'N/A'})",
            get_client_ip(self.request)
        )

    def perform_destroy(self, instance):
        word = instance.word
        audit_service.log_action(
            self.request.user, 'SAFETY', 'DELETE',
            f"删除了违规词: {word}",
            get_client_ip(self.request)
        )
        instance.delete()
from apps.services.chat_service import chat_service
from apps.services.audit_service import audit_service


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ProfileRequiredPermission(permissions.BasePermission):
    """
    安全网权限类：拦截未完善档案（campus_id 为空）的用户访问业务接口。
    结合 DRF 的 TokenAuthentication 使用。
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # 管理员/辅导员不受限制
        if user.role in ('admin', 'counselor'):
            return True
        # 学生必须有 campus_id 才算档案完善
        return bool(user.campus_id)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class WXLoginView(APIView):
    """
    微信静默登录
    仅接收 code，后台自动建档，返回 token + is_profile_completed
    """
    authentication_classes = []  # 登录接口不需要认证
    permission_classes = []

    def post(self, request):
        code = request.data.get('code')

        if not code:
            return Response(
                {"error": "缺少微信登录凭证 code"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. 向微信服务器换取 openid
        appid = settings.WX_APPID
        secret = settings.WX_SECRET
        url = (
            f"https://api.weixin.qq.com/sns/jscode2session"
            f"?appid={appid}&secret={secret}&js_code={code}"
            f"&grant_type=authorization_code"
        )

        try:
            wx_res = requests.get(url, timeout=5).json()
            openid = wx_res.get('openid')
            if not openid:
                return Response(
                    {"error": "微信授权失败", "detail": wx_res.get('errmsg', 'Unknown error')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": f"微信服务器请求异常: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2. 查或创建占位用户（静默建档）
        user, created = User.objects.get_or_create(
            openid=openid,
            defaults={
                'username': f'wx_{openid[:10]}',
                'role': User.RoleChoices.STUDENT
            }
        )

        # 3. 关键判定：用户是否已经补充了必填信息
        is_profile_completed = bool(user.campus_id)

        # 4. 生成/获取 Token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": f"Token {token.key}",
            "is_profile_completed": is_profile_completed,
            "user": UserSerializer(user).data
        })


class CompleteProfileView(APIView):
    """
    渐进式注册：补充用户档案
    必填: campus_id, real_name
    选填: nickname, avatar_url, phone
    """
    def post(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({"error": "未登录"}, status=status.HTTP_401_UNAUTHORIZED)

        campus_id = request.data.get('campus_id', '').strip()
        real_name = request.data.get('real_name', '').strip()

        # Fail-Fast: 必填字段校验
        if not campus_id or not real_name:
            return Response(
                {"error": "学号和真实姓名为必填项"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 更新必填字段
        user.campus_id = campus_id
        user.real_name = real_name

        # 更新选填字段（有值才覆盖）
        nickname = request.data.get('nickname', '').strip()
        avatar_url = request.data.get('avatar_url', '').strip()
        phone = request.data.get('phone', '').strip()

        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url
        if phone:
            user.phone = phone

        user.save()

        return Response({
            "message": "档案补充完成",
            "user": UserSerializer(user).data
        })


class AdminLoginView(APIView):
    """
    真实管理员登录接口
    用于管理后台 Admin-Web
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({"error": "账号密码不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = authenticate(username=username, password=password)
        
        if user is not None and user.role == 'admin':
            # 登录成功，返回真实的 DRF Token
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            })
            
        return Response({"error": "账号或密码错误，或该用户非管理员"}, status=status.HTTP_401_UNAUTHORIZED)


class UserViewSet(viewsets.ModelViewSet):
    """
    学生用户档案管理
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailedSerializer
        return UserSerializer

    def get_queryset(self):
        # 仅限管理员或辅导员查看全量学生
        return self.queryset.filter(role='student')

    def perform_destroy(self, instance):
        # 记录删除学生操作
        handler = self._get_handler()
        audit_service.log_action(
            handler, 'USERS', 'DELETE', 
            f"删除了学生: {instance.real_name} ({instance.campus_id})",
            get_client_ip(self.request)
        )
        instance.delete()

    def _get_handler(self):
        return self.request.user if self.request.user.is_authenticated else None


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    管理聊天会话
    """
    queryset = ChatSession.objects.all().select_related('user')
    permission_classes = [ProfileRequiredPermission] # 仅限完善信息后的用户进入
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'admin':
                return self.queryset
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        handler = request.user
        
        if handler.is_authenticated and handler.role == 'admin':
            audit_service.log_action(
                handler, 'SESSIONS', 'VIEW',
                f"查看了会话聊天记录: ID={instance.id}, 用户={instance.user.real_name if instance.user else '未知'}",
                get_client_ip(request)
            )
            
        return super().retrieve(request, *args, **kwargs)


class ChatInteractView(APIView):
    """
    核心对话交互 API (对接 ChatService 流水线)
    """
    permission_classes = [ProfileRequiredPermission]

    def post(self, request):
        user = request.user
        session_id = request.data.get('session_id')
        content = request.data.get('content')
        selected_node_uuid = request.data.get('selected_node_uuid')  # 新增：用户选择的节点 UUID

        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not content and not selected_node_uuid:
            return Response({"error": "content or selected_node_uuid is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 触发核心 RAG 流水线 (支持两阶段交互)
            result = chat_service.process_message(user, session_id, content, selected_node_uuid=selected_node_uuid)
            return Response(result)
        except Exception as e:
            import traceback
            logger.error(f"Chat interaction error: {str(e)}\n{traceback.format_exc()}")
            return Response({"error": "Internal server error during chat processing."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserMoodLogViewSet(viewsets.ModelViewSet):
    queryset = UserMoodLog.objects.all()
    serializer_class = UserMoodLogSerializer
    permission_classes = [ProfileRequiredPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return UserMoodLog.objects.filter(user=user).order_by('-created_at')
        return UserMoodLog.objects.none()

    def create(self, request, *args, **kwargs):
        """
        情绪打卡 Upsert 逻辑：
        如果用户今日已打卡，则更新记录；否则创建新记录。
        """
        user = request.user
        today = timezone.now().date()
        
        existing_log = UserMoodLog.objects.filter(user=user, created_at=today).first()
        if existing_log:
            # 更新已有记录
            serializer = self.get_serializer(existing_log, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        # 创建新记录
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AssessmentRecordViewSet(viewsets.ModelViewSet):
    """
    学生测评记录管理
    """
    queryset = AssessmentRecord.objects.all()
    serializer_class = AssessmentRecordSerializer
    permission_classes = [ProfileRequiredPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # 学生只能看自己的，管理员可以看全部
            if user.role == 'admin':
                return self.queryset
            return self.queryset.filter(user=user).order_by('-created_at')
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserFavoriteViewSet(viewsets.ModelViewSet):
    queryset = UserFavorite.objects.all()
    serializer_class = UserFavoriteSerializer
    permission_classes = [ProfileRequiredPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return UserFavorite.objects.filter(user=user)
        return UserFavorite.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CrisisAlertLogViewSet(viewsets.ModelViewSet):
    """
    高危预警日志管理（供 Admin 运营后台使用）
    """
    queryset = CrisisAlertLog.objects.all().select_related('user', 'message')
    serializer_class = CrisisAlertLogSerializer

    def get_queryset(self):
        # 运营后台通常可以查看所有预警；如果传入特定 user_id 则用来过滤
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return self.queryset.filter(user_id=user_id)
        return self.queryset
        
    def perform_update(self, serializer):
        # 1. 提取已认证用户
        user = self.request.user if self.request.user.is_authenticated else None
        
        # 2. 接单逻辑：如果状态从 pending 变为 handling/resolved，且目前没有处理人，则自动绑定当前管理员
        if user and user.role == 'admin':
            new_status = serializer.validated_data.get('status')
            if new_status and new_status != 'pending' and not serializer.instance.handler:
                serializer.validated_data['handler'] = user
        
        # 3. 执行单次保存 (原子性生效)
        instance = serializer.save()
        
        # 4. 记录审计日志
        if user and user.role == 'admin':
            audit_service.log_action(
                user, 'ALERTS', 'UPDATE', 
                f"处理了预警工单: ID={instance.id}, 目标状态={instance.status}",
                get_client_ip(self.request)
            )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    系统审计日志查看
    """
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        # 仅限管理员查看审计日志
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return AuditLog.objects.select_related('admin').all().order_by('-created_at')
        return AuditLog.objects.none()


from rest_framework import viewsets, status, permissions, filters

class ArticleViewSet(viewsets.ModelViewSet):
    """
    科普文章管理 (CMS)
    """
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    lookup_field = 'id'  # 明确指定查找字段为 id
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'author']

    def perform_create(self, serializer):
        import uuid
        new_uuid = str(uuid.uuid4())
        instance = serializer.save(id=new_uuid)
        
        # 自动同步创建图谱节点
        query = '''
        MERGE (n:`心理文章` {uuid: $uuid})
        SET n.名称 = $title, n.`封面图` = $cover, n.url = $url, n.`描述` = ''
        '''
        try:
            from apps.repositories.neo4j_repo import neo4j_repo
            with neo4j_repo.driver.session() as session:
                session.run(query, uuid=new_uuid, title=instance.title, cover=instance.cover_image or '', url=instance.id)
        except Exception as e:
            import logging
            logging.error(f"Failed to create Neo4j node for article {instance.id}: {str(e)}")
            # Even if graph creation fails, the mysql record is saved, but we log the error

        handler = self._get_handler()
        if handler:
            audit_service.log_action(
                handler, 'ARTICLES', 'CREATE',
                f"发布了新文章: {instance.title} (ID={instance.id})",
                get_client_ip(self.request)
            )

    def perform_update(self, serializer):
        handler = self._get_handler()
        instance = serializer.save()
        
        # 同步更新图谱节点
        query = '''
        MATCH (n:`心理文章` {uuid: $uuid})
        SET n.名称 = $title, n.`封面图` = $cover
        '''
        try:
            from apps.repositories.neo4j_repo import neo4j_repo
            with neo4j_repo.driver.session() as session:
                session.run(query, uuid=instance.id, title=instance.title, cover=instance.cover_image or '')
        except Exception as e:
            import logging
            logging.error(f"Failed to update Neo4j node for article {instance.id}: {str(e)}")

        if handler:
            audit_service.log_action(
                handler, 'ARTICLES', 'UPDATE',
                f"更新了文章: {instance.title} (ID={instance.id})",
                get_client_ip(self.request)
            )

    def perform_destroy(self, instance):
        node_id = instance.id
        node_title = instance.title
        try:
            from apps.repositories.neo4j_repo import neo4j_repo
            query = "MATCH (n:`心理文章`) WHERE n.uuid = $uuid DETACH DELETE n"
            with neo4j_repo.driver.session() as session:
                session.run(query, uuid=node_id)
        except Exception as e:
            import logging
            logging.error(f"Failed to delete Neo4j node for article {node_id}: {str(e)}")

        handler = self._get_handler()
        if handler:
            audit_service.log_action(
                handler, 'ARTICLES', 'DELETE',
                f"删除了文章: {node_title} (ID={node_id})",
                get_client_ip(self.request)
            )
        instance.delete()

    def _get_handler(self):
        return self.request.user if self.request.user.is_authenticated else None

    @action(detail=True, methods=['get'], url_path='stats', url_name='stats')
    def stats(self, request, id=None, **kwargs):
        """
        获取文章详情页统计数据: 收藏总数、评论总数、过去7天趋势
        """
        # 调试日志：确认请求到达
        logger.info(f"Fetching stats for article ID: {id or kwargs.get('id')}")
        instance = self.get_object()
        now = timezone.now()
        
        # 统计数据
        total_favorites = UserFavorite.objects.filter(target_type='Article', target_id=instance.id).count()
        total_comments = instance.comments.count()
        
        # 过去 7 天趋势
        daily_stats = []
        for i in range(6, -1, -1):
            date = (now - timezone.timedelta(days=i)).date()
            f_count = UserFavorite.objects.filter(
                target_type='Article', 
                target_id=instance.id,
                created_at__date=date
            ).count()
            c_count = instance.comments.filter(created_at__date=date).count()
            daily_stats.append({
                "date": date.strftime('%m-%d'),
                "favorites": f_count,
                "comments": c_count
            })
            
        return Response({
            "total_favorites": total_favorites,
            "total_comments": total_comments,
            "daily_stats": daily_stats
        })



class AssessmentScaleViewSet(viewsets.ModelViewSet):
    """
    心理量表管理
    """
    queryset = AssessmentScale.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentScaleListSerializer
        return AssessmentScaleSerializer

    def perform_create(self, serializer):
        import uuid
        # 如果请求中已经带了 ID（如种子脚本），则优先使用提供的 ID
        provided_id = self.request.data.get('id')
        if provided_id:
            new_uuid = provided_id
        else:
            new_uuid = str(uuid.uuid4())
        
        instance = serializer.save(id=new_uuid)

        
        # 自动同步创建图谱节点
        query = '''
        CREATE (n:`测评量表` {uuid: $uuid, 名称: $name, 描述: '', url: $url})
        '''
        try:
            from apps.repositories.neo4j_repo import neo4j_repo
            with neo4j_repo.driver.session() as session:
                session.run(query, uuid=new_uuid, name=instance.name, url=instance.id)
        except Exception as e:
            import logging
            logging.error(f"Failed to create Neo4j node for scale {instance.id}: {str(e)}")

        handler = self._get_handler()
        if handler:
            audit_service.log_action(
                handler, 'SCALES', 'CREATE',
                f"发布了新量表: {instance.name} (ID={instance.id})",
                get_client_ip(self.request)
            )

    def perform_destroy(self, instance):
        node_id = instance.id
        node_name = instance.name
        try:
            from apps.repositories.neo4j_repo import neo4j_repo
            query = "MATCH (n:`测评量表`) WHERE n.uuid = $uuid DETACH DELETE n"
            with neo4j_repo.driver.session() as session:
                session.run(query, uuid=node_id)
        except Exception as e:
            import logging
            logging.error(f"Failed to delete Neo4j node for scale {node_id}: {str(e)}")

        handler = self._get_handler()
        if handler:
            audit_service.log_action(
                handler, 'SCALES', 'DELETE',
                f"删除了量表: {node_name} (ID={node_id})",
                get_client_ip(self.request)
            )
        instance.delete()

    @action(detail=True, methods=['post'])
    def sync_questions(self, request, pk=None):
        """
        全量同步更新题目（覆盖模式）
        """
        scale = self.get_object()
        questions_data = request.data.get('questions', [])
        
        # 简单处理：先全部删除再重新创建
        scale.questions.all().delete()
        for i, q in enumerate(questions_data):
            AssessmentQuestion.objects.create(
                scale=scale,
                sort_order=q.get('sort_order', i+1),
                content=q.get('content'),
                options=q.get('options')
            )
        
        # 更新题数统计
        scale.question_count = len(questions_data)
        scale.save(update_fields=['question_count'])
        
        # 审计日志
        handler = self._get_handler()
        if handler:
            audit_service.log_action(
                handler, 'SCALES', 'UPDATE',
                f"更新了量表题库: {scale.name} (ID={scale.id}, 题数={scale.question_count})",
                get_client_ip(request)
            )
            
        return Response({"status": "questions synced"})

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开启测评会话 POST /api/scales/{id}/start/"""
        from apps.services.assessment_service import assessment_service
        try:
            session_id, first_q = assessment_service.start_session(request.user.id, pk)
            return Response({
                "session_id": session_id,
                "question": AssessmentQuestionSerializer(first_q).data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='submit-step')
    def submit_step(self, request):
        """提交当前答案并获取下一题 POST /api/scales/submit-step/"""
        from apps.services.assessment_service import assessment_service
        session_id = request.data.get('session_id')
        q_id = request.data.get('q_id')
        option_label = request.data.get('label')
        score = request.data.get('score')

        if not all([session_id, q_id, score]):
            return Response({"error": "Missing params"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            next_q, is_finished = assessment_service.submit_answer(session_id, q_id, option_label, score)
            
            if is_finished:
                report = assessment_service.generate_final_report(request.user.id, session_id)
                
                # [新增] 闭环逻辑：如果有关联的触发消息，更新其状态并生成回馈
                trigger_msg_id = request.data.get('trigger_msg_id')
                if trigger_msg_id:
                    try:
                        msg = ChatMessage.objects.get(id=trigger_msg_id)
                        # 更新卡片状态为已完成
                        if not msg.suggested_assessment:
                            msg.suggested_assessment = {}
                        msg.suggested_assessment['is_completed'] = True
                        msg.suggested_assessment['result'] = {
                            'score': report.get('total_score'),
                            'level': report.get('level'),
                            'record_id': report.get('record_id')
                        }
                        msg.save()
                        
                        # 由 AI 发起针对性的回馈回复
                        chat_service.generate_assessment_feedback(request.user, msg.session.id, report)
                    except ChatMessage.DoesNotExist:
                        logger.warning(f"Trigger message {trigger_msg_id} not found during assessment completion.")

                audit_service.log_action(
                    request.user, 'ASSESSMENT', 'COMPLETED',
                    f"完成了测评: {report.get('scale_name', '未知量表')}, 得分: {report.get('total_score')}",
                    get_client_ip(request)
                )
                return Response({"is_finished": True, "report": report})
            
            return Response({
                "is_finished": False,
                "next_question": AssessmentQuestionSerializer(next_q).data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.parsers import MultiPartParser
from apps.api.utils.tencent_asr import TencentASR

class STTAPIView(APIView):
    """
    语音转文字 (STT) 接口
    """
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if 'audio' not in request.FILES:
            return Response({'error': 'No audio file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
        
        audio_file = request.FILES['audio']
        file_size = audio_file.size
        content_type = audio_file.content_type
        
        print(f"DEBUG: Received audio file: {audio_file.name}, size: {file_size} bytes, type: {content_type}")

        if file_size < 100:
            return Response({'error': f'Audio file too small ({file_size} bytes)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取文件名后缀或内容类型作为格式
        voice_format = audio_file.name.split('.')[-1].lower()
        if voice_format not in ['mp3', 'm4a', 'wav', 'pcm', 'aac']:
            # 如果从后缀看不出来，尝试根据 hex 特征识别（备选逻辑）
            voice_format = 'aac' 
            
        try:
            audio_file.seek(0)
            audio_data = audio_file.read()
            
            # 调试：打印前20个字节的十六进制
            print(f"DEBUG: Audio Start Bytes (hex): {audio_data[:20].hex()}")
            
            asr_service = TencentASR()
            text = asr_service.speech_to_text(audio_data, voice_format=voice_format)
            print(f"DEBUG: ASR Result: {text}")
            
            logger.info(f"ASR Result: {text}")
            return Response({'text': text})
        except Exception as e:
            logger.error(f"ASR processing failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# region 引导性问题系统 (Conversation Starters)
class GuidanceQuestionListView(APIView):
    """
    对话启动器：返回随机引导问题。
    GET /api/guidance-questions/?count=4&category=academic
    - count: 返回数量（默认 4，上限 8）
    - category: 按类别过滤（可选）
    """
    permission_classes = [permissions.AllowAny]

    # 防止滥用的硬性上限
    MAX_RETURN_COUNT = 8

    def get(self, request):
        count = min(
            int(request.query_params.get('count', 4)),
            self.MAX_RETURN_COUNT
        )
        category = request.query_params.get('category')

        queryset = GuidanceQuestion.objects.filter(is_active=True)

        # 如果前端传了 category，进行过滤
        if category:
            queryset = queryset.filter(category=category)

        # 随机返回指定数量
        questions = queryset.order_by('?')[:count]
        serializer = GuidanceQuestionSerializer(questions, many=True)
        return Response(serializer.data)


class UserFavoriteViewSet(viewsets.ModelViewSet):
    """
    用户收藏管理: 支持对文章、知识点等的增删改查
    """
    serializer_class = UserFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 仅返回且只能看到自己的收藏
        return UserFavorite.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # 覆写 create 逻辑以支持接口幂等性，防止重复收藏报错
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        target_type = serializer.validated_data.get('target_type')
        target_id = serializer.validated_data.get('target_id')
        
        # 使用 get_or_create 确保数据库层面的幂等
        obj, created = UserFavorite.objects.get_or_create(
            user=self.request.user,
            target_type=target_type,
            target_id=target_id,
            defaults={'target_title': serializer.validated_data.get('target_title', '')}
        )
        
        # 如果已经存在，直接返回其序列化结果
        if not created:
            return Response(self.get_serializer(obj).data, status=status.HTTP_200_OK)
            
        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED)
# endregion

# region 文章评论系统 (Article Comment System)
from apps.services.crisis_service import crisis_interceptor

class ArticleCommentViewSet(viewsets.ModelViewSet):
    """
    文章评论管理 (支持评论与一级回复)
    """
    queryset = ArticleComment.objects.filter(is_audit_passed=True, parent__isnull=True)
    serializer_class = ArticleCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        content = self.request.data.get('content', '')
        # 敏感词硬拦截校验
        crisis_check = crisis_interceptor.fast_check(content)
        
        is_passed = True
        if crisis_check:
            # 如果命中了风险词，标记为待审核/不通过
            is_passed = False
            logger.warning(f"Comment by User {self.request.user.id} hit crisis keywords: {content[:50]}...")

        instance = serializer.save(user=self.request.user, is_audit_passed=is_passed)
        
        if not is_passed:
            # 记录审计日志
            from apps.services.audit_service import audit_service
            audit_service.log_action(
                self.request.user, 'COMMENTS', 'BLOCK',
                f"提交的评论包含敏感内容被拦截: {content[:30]}",
                get_client_ip(self.request)
            )

    def get_queryset(self):
        # 如果是管理员，可以看到所有评论（包括未过审的）进行审核
        article_id = self.request.query_params.get('article')
        qs = ArticleComment.objects.filter(parent__isnull=True)
        
        if article_id:
            qs = qs.filter(article_id=article_id)
            
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return qs.order_by('-created_at')
            
        return qs.filter(is_audit_passed=True).order_by('-created_at')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def audit(self, request, pk=None):
        """管理员审核操作"""
        comment = self.get_object()
        is_passed = request.data.get('is_passed', True)
        comment.is_audit_passed = is_passed
        comment.save()
        return Response({"status": "audited", "is_passed": is_passed})
# endregion

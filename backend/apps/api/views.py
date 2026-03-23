import requests
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.utils import timezone
from apps.models import (
    User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, 
    UserFavorite, AssessmentRecord, AuditLog, Article, AssessmentScale, AssessmentQuestion
)
from apps.api.serializers import (
    UserSerializer, UserDetailedSerializer, ChatSessionSerializer, ChatSessionListSerializer,
    ChatMessageSerializer, CrisisAlertLogSerializer, UserMoodLogSerializer, UserFavoriteSerializer, 
    AuditLogSerializer, ArticleSerializer, AssessmentScaleSerializer, AssessmentScaleListSerializer,
    AssessmentQuestionSerializer, AssessmentRecordSerializer
)
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

        if not all([session_id, content]):
            return Response({"error": "session_id and content are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 触发核心 RAG 流水线
            result = chat_service.process_message(user, session_id, content)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class ArticleViewSet(viewsets.ModelViewSet):
    """
    科普文章管理 (CMS)
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def perform_create(self, serializer):
        import uuid
        new_uuid = str(uuid.uuid4())
        instance = serializer.save(id=new_uuid)
        
        # 自动同步创建图谱节点
        query = '''
        CREATE (n:`心理文章` {uuid: $uuid, 名称: $title, 描述: '', url: $url})
        '''
        try:
            from apps.repositories.neo4j_repo import neo4j_repo
            with neo4j_repo.driver.session() as session:
                session.run(query, uuid=new_uuid, title=instance.title, url=instance.id)
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

    def _get_handler(self):
        return self.request.user if self.request.user.is_authenticated else None

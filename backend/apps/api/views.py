from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from apps.models import (
    User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, 
    UserFavorite, AssessmentRecord, AuditLog, Article, AssessmentScale, AssessmentQuestion
)
from apps.api.serializers import (
    UserSerializer, UserDetailedSerializer, ChatSessionSerializer, ChatSessionListSerializer,
    ChatMessageSerializer, CrisisAlertLogSerializer, UserMoodLogSerializer, UserFavoriteSerializer, 
    AuditLogSerializer, ArticleSerializer, AssessmentScaleSerializer, AssessmentScaleListSerializer,
    AssessmentQuestionSerializer
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


class MockLoginView(APIView):
    """
    模拟微信小程序登录（无密码，直接以 campus_id 或 openid 获取/创建用户）
    仅供开发阶段测试使用。
    """
    def post(self, request):
        campus_id = request.data.get('campus_id')
        nickname = request.data.get('nickname', '匿名同学')
        
        if not campus_id:
            return Response({"error": "campus_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        user, created = User.objects.get_or_create(
            campus_id=campus_id,
            defaults={'username': f'stu_{campus_id}', 'nickname': nickname}
        )
        return Response({
            "token": str(user.id),  # 暂时用 user UUID 模拟 token
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
            # 登录成功，返回 token (为了简配，我们复用 user.id 充当 token)
            return Response({
                "token": str(user.id),
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
        auth_token = self.request.META.get('HTTP_AUTHORIZATION')
        return User.objects.filter(id=auth_token).first() if auth_token else None



class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    管理聊天会话
    """
    queryset = ChatSession.objects.all().select_related('user')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        auth_token = self.request.META.get('HTTP_AUTHORIZATION')
        if not auth_token:
            return self.queryset.none()
            
        user = User.objects.filter(id=auth_token).first()
        if user and user.role == 'admin':
            return self.queryset
            
        return ChatSession.objects.filter(user_id=auth_token)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        
        handler = User.objects.filter(id=auth_token).first()
        if handler and handler.role == 'admin':
            audit_service.log_action(
                handler, 'SESSIONS', 'VIEW',
                f"查看了会话聊天记录: ID={instance.id}, 用户={instance.user.real_name if instance.user else '未知'}",
                get_client_ip(request)
            )
            
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        user_id = self.request.META.get('HTTP_AUTHORIZATION')
        if not user_id:
             user_id = self.request.data.get('user_id') # 降级方案
        user = get_object_or_404(User, id=user_id)
        serializer.save(user=user)


class ChatInteractView(APIView):
    """
    核心对话交互 API (对接 ChatService 流水线)
    """
    def post(self, request):
        user_id = request.META.get('HTTP_AUTHORIZATION') or request.data.get('user_id')
        session_id = request.data.get('session_id')
        content = request.data.get('content')

        if not all([user_id, session_id, content]):
            return Response({"error": "user_id, session_id, and content are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, id=user_id)
        
        try:
            # 触发核心 RAG 流水线
            result = chat_service.process_message(user, session_id, content)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserMoodLogViewSet(viewsets.ModelViewSet):
    queryset = UserMoodLog.objects.all()
    serializer_class = UserMoodLogSerializer

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_AUTHORIZATION')
        if user_id:
            return UserMoodLog.objects.filter(user_id=user_id)
        return self.queryset


class UserFavoriteViewSet(viewsets.ModelViewSet):
    queryset = UserFavorite.objects.all()
    serializer_class = UserFavoriteSerializer

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_AUTHORIZATION')
        if user_id:
            return UserFavorite.objects.filter(user_id=user_id)
        return self.queryset


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
        # 1. 提取身份标识
        auth_token = self.request.META.get('HTTP_AUTHORIZATION')
        user = User.objects.filter(id=auth_token).first() if auth_token else None
        
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
        auth_token = self.request.META.get('HTTP_AUTHORIZATION')
        user = User.objects.filter(id=auth_token).first() if auth_token else None
        
        if user and user.role == 'admin':
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
        auth_token = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_token == 'admin_mock_token_123':
            handler, _ = User.objects.get_or_create(
                username='admin', 
                defaults={'role': 'admin', 'real_name': '超级管理员'}
            )
            return handler
        return User.objects.filter(id=auth_token).first() if auth_token else None


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
        auth_token = self.request.META.get('HTTP_AUTHORIZATION')
        return User.objects.filter(id=auth_token).first() if auth_token else None


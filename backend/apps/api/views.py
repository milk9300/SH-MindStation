from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from apps.models import User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, UserFavorite
from apps.api.serializers import (
    UserSerializer, ChatSessionSerializer, ChatMessageSerializer, 
    CrisisAlertLogSerializer, UserMoodLogSerializer, UserFavoriteSerializer
)
from apps.services.chat_service import chat_service

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


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    管理聊天会话
    """
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        # 实际开发中应该从 request.user 获取，这里我们用 Header 里的 Auth 作为 UserID 模拟
        user_id = self.request.META.get('HTTP_AUTHORIZATION')
        if user_id:
            return ChatSession.objects.filter(user_id=user_id)
        return self.queryset

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

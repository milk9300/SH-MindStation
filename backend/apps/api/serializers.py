from rest_framework import serializers
from apps.models import (
    User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, 
    UserFavorite, AssessmentRecord, AuditLog, Article, AssessmentScale, AssessmentQuestion
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'campus_id', 'real_name', 'nickname', 'avatar_url', 'phone']


class AssessmentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentRecord
        fields = '__all__'
        read_only_fields = ['user']


class UserMoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMoodLog
        fields = '__all__'
        read_only_fields = ['user']


class UserDetailedSerializer(serializers.ModelSerializer):
    mood_logs = UserMoodLogSerializer(many=True, read_only=True)
    assessments = AssessmentRecordSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'campus_id', 'real_name', 'nickname', 
            'avatar_url', 'phone', 'mood_logs', 'assessments'
        ]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'role', 'content', 'structured_cards', 'intent_type', 'created_at']


class ChatSessionListSerializer(serializers.ModelSerializer):
    """用于列表展示，不包含敏感聊天内容"""
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'updated_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """包含完整聊天对话流，用于深度审计"""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'messages']


class CrisisAlertLogSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    message_content = serializers.CharField(source='message.content', read_only=True)
    handler_name = serializers.CharField(source='handler.real_name', read_only=True, default='')

    class Meta:
        model = CrisisAlertLog
        fields = '__all__'
        
    def get_user_info(self, obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "username": obj.user.username,
                "campus_id": obj.user.campus_id,
                "real_name": obj.user.real_name
            }
        return None


class UserFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorite
        fields = '__all__'
        read_only_fields = ['user']


class AuditLogSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.real_name', read_only=True, default='Unknown')

    class Meta:
        model = AuditLog
        fields = ['id', 'admin', 'admin_name', 'action_module', 'action_type', 'target_detail', 'ip_address', 'created_at']


class ArticleSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = Article
        fields = '__all__'

class AssessmentQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentQuestion
        fields = ['id', 'sort_order', 'content', 'options']


class AssessmentScaleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentScale
        fields = ['id', 'name', 'description', 'question_count', 'created_at']


class AssessmentScaleSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    questions = AssessmentQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = AssessmentScale
        fields = ['id', 'name', 'description', 'question_count', 'scoring_rules', 'questions', 'created_at']


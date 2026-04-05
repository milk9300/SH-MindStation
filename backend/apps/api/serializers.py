from rest_framework import serializers
from apps.models import (
    User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, 
    UserFavorite, AssessmentRecord, AuditLog, Article, AssessmentScale, 
    AssessmentQuestion, CrisisKeyword, RiskLevel, EmergencyPlan, GuidanceQuestion,
    ArticleComment
)

class RiskLevelSerializer(serializers.ModelSerializer):
    """
    风险等级序列化器
    level 和 color 字段用于对接 Vite 前端组件 (RiskLevelsView.vue)
    """
    level = serializers.IntegerField(source='priority', required=False)
    color = serializers.CharField(source='color_code', required=False)
    
    class Meta:
        model = RiskLevel
        fields = ['id', 'name', 'description', 'score_range', 'color', 'level', 'priority', 'color_code']
        read_only_fields = ['level', 'color']

    def get_level(self, obj):
        return obj.priority

    def get_color(self, obj):
        return obj.color_code

class EmergencyPlanSerializer(serializers.ModelSerializer):
    risk_level_name = serializers.CharField(source='risk_level.name', read_only=True)
    risk_level_color = serializers.CharField(source='risk_level.color_code', read_only=True)
    
    class Meta:
        model = EmergencyPlan
        fields = '__all__'

class CrisisKeywordSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)
    level_color = serializers.CharField(source='level.color_code', read_only=True)
    
    class Meta:
        model = CrisisKeyword
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'campus_id', 'real_name', 'nickname', 'avatar_url', 'phone']

    def get_avatar_url(self, obj):
        if not obj.avatar_url:
            return None
        if obj.avatar_url.startswith(('http://', 'https://')):
            return obj.avatar_url
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri('/' + obj.avatar_url.lstrip('/'))
        return obj.avatar_url


class AssessmentRecordSerializer(serializers.ModelSerializer):
    recommendations = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentRecord
        fields = '__all__'
        read_only_fields = ['user']

    def get_recommendations(self, obj):
        from apps.services.assessment_service import assessment_service
        recommendations = {}
        if obj.dimension_scores:
            for dim, score in obj.dimension_scores.items():
                if score > 3:
                    recommendations[dim] = assessment_service._fetch_graph_resources(dim)
        return recommendations


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
    cards = serializers.JSONField(source='structured_cards', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'role', 'content', 'cards', 'suggested_assessment', 'knowledge_base_uuid', 'intent_type', 'created_at']


class ChatSessionListSerializer(serializers.ModelSerializer):
    """用于列表展示，不包含敏感聊天内容"""
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'updated_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """包含完整聊天对话流，用于深度审计与历史恢复"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    current_slots = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'updated_at', 'messages', 'current_slots']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'messages', 'current_slots']

    def get_current_slots(self, obj):
        from apps.services.chat_service import chat_service
        return chat_service._get_session_slots(str(obj.id))



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
    cover_image = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = '__all__'

    def get_favorite_count(self, obj):
        return UserFavorite.objects.filter(target_type='Article', target_id=obj.id).count()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_cover_image(self, obj):
        if not obj.cover_image:
            return None
        if obj.cover_image.startswith(('http://', 'https://')):
            return obj.cover_image
        
        request = self.context.get('request')
        # 如果有 request，构建完整的绝对路径
        if request:
            return request.build_absolute_uri('/' + obj.cover_image.lstrip('/'))
        
        # 兼容性处理：如果没有请求上下文（如后台任务），则根据 settings 中的 BACKEND_URL 构建
        from django.conf import settings
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
        return f"{backend_url}/{obj.cover_image.lstrip('/')}"


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


class GuidanceQuestionSerializer(serializers.ModelSerializer):
    """对话启动器序列化"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = GuidanceQuestion
        fields = ['id', 'text', 'category', 'category_display', 'sort_order', 'is_active']


class ArticleCommentSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ArticleComment
        fields = ['id', 'article', 'user', 'user_nickname', 'user_avatar', 'content', 'parent', 'is_audit_passed', 'created_at', 'replies']
        read_only_fields = ['user', 'is_audit_passed']

    def get_user_avatar(self, obj):
        if not obj.user.avatar_url:
            return None
        if obj.user.avatar_url.startswith(('http://', 'https://')):
            return obj.user.avatar_url
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri('/' + obj.user.avatar_url.lstrip('/'))
        return obj.user.avatar_url

    def get_replies(self, obj):
        # 仅返回一级回复，支持树状结构但在序列化时扁平化
        if obj.parent_id is None:
            replies = ArticleComment.objects.filter(parent=obj, is_audit_passed=True)
            return ArticleCommentSerializer(replies, many=True, context=self.context).data
        return []

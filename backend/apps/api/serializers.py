from rest_framework import serializers
from apps.models import User, ChatSession, ChatMessage, CrisisAlertLog, UserMoodLog, UserFavorite

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'campus_id', 'real_name', 'nickname', 'avatar_url', 'phone']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'role', 'content', 'structured_cards', 'intent_type', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'messages']


class CrisisAlertLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrisisAlertLog
        fields = '__all__'


class UserMoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMoodLog
        fields = '__all__'


class UserFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorite
        fields = '__all__'

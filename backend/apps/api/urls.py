from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MockLoginView,
    ChatSessionViewSet,
    ChatInteractView,
    UserMoodLogViewSet,
    UserFavoriteViewSet
)

router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='session')
router.register(r'moods', UserMoodLogViewSet, basename='mood')
router.register(r'favorites', UserFavoriteViewSet, basename='favorite')

urlpatterns = [
    path('auth/login/', MockLoginView.as_view(), name='auth-login'),
    path('chat/interact/', ChatInteractView.as_view(), name='chat-interact'),
    path('', include(router.urls)),
]

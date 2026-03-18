from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MockLoginView,
    AdminLoginView,
    UserViewSet,
    ChatSessionViewSet,
    ChatInteractView,
    UserMoodLogViewSet,
    UserFavoriteViewSet,
    CrisisAlertLogViewSet,
    AuditLogViewSet,
    ArticleViewSet,
    AssessmentScaleViewSet
)
from .graph_views import GraphDumpView, EntityDetailView, EdgeManagementView, EntitySearchView, EntityCreateView
from .stats_views import DashboardStatsView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sessions', ChatSessionViewSet, basename='session')
router.register(r'moods', UserMoodLogViewSet, basename='mood')
router.register(r'favorites', UserFavoriteViewSet, basename='favorite')
router.register(r'alerts', CrisisAlertLogViewSet, basename='alert')
router.register(r'audit', AuditLogViewSet, basename='audit')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'scales', AssessmentScaleViewSet, basename='scale')


urlpatterns = [
    path('auth/login/', MockLoginView.as_view(), name='auth-login'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('chat/interact/', ChatInteractView.as_view(), name='chat-interact'),
    path('graph/dump/', GraphDumpView.as_view(), name='graph-dump'),
    path('graph/entity/create/', EntityCreateView.as_view(), name='entity-create'),
    path('graph/entity/<str:node_id>/', EntityDetailView.as_view(), name='entity-detail'),
    path('graph/edge/', EdgeManagementView.as_view(), name='edge-management'),
    path('graph/search/', EntitySearchView.as_view(), name='entity-search'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WXLoginView,
    CompleteProfileView,
    AdminLoginView,
    UserViewSet,
    ChatSessionViewSet,
    ChatInteractView,
    UserMoodLogViewSet,
    UserFavoriteViewSet,
    CrisisAlertLogViewSet,
    AuditLogViewSet,
    ArticleViewSet,
    AssessmentScaleViewSet,
    AssessmentRecordViewSet,
    CrisisKeywordViewSet,
    RiskLevelViewSet,
    EmergencyPlanViewSet,
    STTAPIView,
    GuidanceQuestionListView,
    ArticleCommentViewSet
)
from .graph_views import (
    GraphDumpView, EntityDetailView, EdgeManagementView, EntitySearchView, EntityCreateView,
    KnowledgeDetailView, KnowledgeHomeView, EntityNeighborsView
)
from .stats_views import DashboardStatsView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'chat-sessions', ChatSessionViewSet, basename='chat-session')
router.register(r'moods', UserMoodLogViewSet, basename='mood')
router.register(r'favorites', UserFavoriteViewSet, basename='favorite')
router.register(r'alerts', CrisisAlertLogViewSet, basename='alert')
router.register(r'audit', AuditLogViewSet, basename='audit')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'scales', AssessmentScaleViewSet, basename='scale')
router.register(r'assessments', AssessmentRecordViewSet, basename='assessment')
router.register(r'crisis-keywords', CrisisKeywordViewSet, basename='crisis-keyword')
router.register(r'risk-levels', RiskLevelViewSet, basename='risk-level')
router.register(r'emergency-plans', EmergencyPlanViewSet, basename='emergency-plan')
router.register('article-comments', ArticleCommentViewSet, basename='article-comment')


urlpatterns = [
    path('auth/login/', WXLoginView.as_view(), name='auth-login'),
    path('auth/complete-profile/', CompleteProfileView.as_view(), name='auth-complete-profile'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('chat/interact/', ChatInteractView.as_view(), name='chat-interact'),
    path('graph/dump/', GraphDumpView.as_view(), name='graph-dump'),
    path('graph/entity/create/', EntityCreateView.as_view(), name='entity-create'),
    path('graph/entity/<str:node_id>/', EntityDetailView.as_view(), name='entity-detail'),
    path('graph/entity/<str:node_id>/neighbors/', EntityNeighborsView.as_view(), name='entity-neighbors'),
    path('graph/knowledge-base/home/', KnowledgeHomeView.as_view(), name='knowledge-base-home'),
    path('graph/knowledge-base/<str:uuid>/', KnowledgeDetailView.as_view(), name='knowledge-base-detail'),
    path('graph/edge/', EdgeManagementView.as_view(), name='edge-management'),
    path('graph/search/', EntitySearchView.as_view(), name='entity-search'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('chat/stt/', STTAPIView.as_view(), name='chat-stt'),
    path('guidance-questions/', GuidanceQuestionListView.as_view(), name='guidance-questions'),
    path('', include(router.urls)),
]

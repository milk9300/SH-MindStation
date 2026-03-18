import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    sys_user: 统一身份认证与用户表
    """
    class RoleChoices(models.TextChoices):
        STUDENT = 'student', '学生'
        COUNSELOR = 'counselor', '辅导员'
        ADMIN = 'admin', '管理员'

    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.STUDENT)
    openid = models.CharField("微信 OpenID", max_length=128, unique=True, null=True, blank=True)
    campus_id = models.CharField("学号/教工号", max_length=50, null=True, blank=True)
    real_name = models.CharField("真实姓名", max_length=50, null=True, blank=True)
    nickname = models.CharField("昵称", max_length=100, default='匿名同学')
    avatar_url = models.CharField("头像链接", max_length=200, null=True, blank=True)
    phone = models.CharField("联系电话", max_length=20, null=True, blank=True)
    
    class Meta:
        db_table = 'sys_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class ChatSession(models.Model):
    """
    biz_chat_session: 多轮对话会话表
    """
    id = models.CharField("会话ID", primary_key=True, max_length=64, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField("会话主题", max_length=100, default='新的咨询')
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = 'biz_chat_session'
        ordering = ['-updated_at']


class ChatMessage(models.Model):
    """
    biz_chat_message: 多模态聊天消息表
    """
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField("消息角色", max_length=10) # user / ai
    content = models.TextField("文本内容")
    structured_cards = models.JSONField("图谱结构化数据", default=list, blank=True)
    intent_type = models.CharField("意图类型", max_length=50, null=True, blank=True)
    created_at = models.DateTimeField("发送时间", auto_now_add=True)

    class Meta:
        db_table = 'biz_chat_message'
        ordering = ['created_at']


class CrisisAlertLog(models.Model):
    """
    sec_crisis_alert_log: 高危预警审计表
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', '待处理'
        HANDLING = 'handling', '处理中'
        RESOLVED = 'resolved', '已解决'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crisis_alerts')
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_alerts')
    message = models.OneToOneField(ChatMessage, on_delete=models.CASCADE)
    risk_level = models.CharField("风险等级", max_length=20)
    trigger_symptom = models.CharField("触发症状", max_length=100)
    status = models.CharField("处理状态", max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    handler_remark = models.TextField("跟进备注", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = 'sec_crisis_alert_log'
        ordering = ['-created_at']


class UserMoodLog(models.Model):
    """
    biz_user_mood_log: 用户情绪打卡表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_logs')
    mood_level = models.IntegerField("情绪指数") # 1-5
    mood_tag = models.CharField("情绪标签", max_length=50, null=True, blank=True)
    note = models.TextField("打卡备注", null=True, blank=True)
    created_at = models.DateField("打卡日期", auto_now_add=True)

    class Meta:
        db_table = 'biz_user_mood_log'
        unique_together = ('user', 'created_at')
        ordering = ['-created_at']


class UserFavorite(models.Model):
    """
    biz_user_favorite: 用户收藏表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    target_type = models.CharField("目标类型", max_length=50) # Article, Treatment, Policy
    target_id = models.CharField("目标UUID", max_length=128)
    target_title = models.CharField("目标标题", max_length=200)
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        db_table = 'biz_user_favorite'
        unique_together = ('user', 'target_type', 'target_id')
        ordering = ['-created_at']


class AssessmentRecord(models.Model):
    """
    biz_assessment_record: 测评记录表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    scale_name = models.CharField("量表名称", max_length=100)
    total_score = models.IntegerField("总得分")
    result_level = models.CharField("测评结果", max_length=50)
    report_json = models.JSONField("详细得分", null=True, blank=True)
    created_at = models.DateTimeField("测评时间", auto_now_add=True)

    class Meta:
        db_table = 'biz_assessment_record'
        ordering = ['-created_at']


class Article(models.Model):
    """
    biz_article: 科普文章表 (CMS)
    """
    id = models.CharField("文章ID", primary_key=True, max_length=64) # 与 Neo4j UUID 一致
    title = models.CharField("文章标题", max_length=200)
    cover_image = models.CharField("封面图URL", max_length=500, null=True, blank=True)
    content = models.TextField("文章内容") # 富文本或 Markdown
    author = models.CharField("作者/机构", max_length=50, default='心理中心')
    status = models.CharField("发布状态", max_length=20, default='published') # draft / published
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = 'biz_article'
        ordering = ['-created_at']


class AssessmentScale(models.Model):
    """
    biz_assessment_scale: 心理量表主表
    """
    id = models.CharField("量表ID", primary_key=True, max_length=64) # 与 Neo4j UUID 一致
    name = models.CharField("量表名称", max_length=100)
    description = models.TextField("量表指导语", null=True, blank=True)
    question_count = models.IntegerField("题目总数", default=0)
    scoring_rules = models.JSONField("计分与评级规则", default=list) # [{"min": 0, "max": 10, "result": "正常"}]
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = 'biz_assessment_scale'
        ordering = ['-created_at']


class AssessmentQuestion(models.Model):
    """
    biz_assessment_question: 量表题目表
    """
    scale = models.ForeignKey(AssessmentScale, on_delete=models.CASCADE, related_name='questions')
    sort_order = models.IntegerField("题号")
    content = models.CharField("题干内容", max_length=500)
    options = models.JSONField("选项与分值") # [{"label": "没有", "score": 1}]

    class Meta:
        db_table = 'biz_assessment_question'
        ordering = ['sort_order']


class AuditLog(models.Model):
    """
    sys_audit_log: 系统审计日志表
    """
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action_module = models.CharField("操作模块", max_length=50)
    action_type = models.CharField("操作类型", max_length=20)
    target_detail = models.TextField("操作详情", null=True, blank=True)
    ip_address = models.CharField("操作IPv4", max_length=50, null=True, blank=True)
    created_at = models.DateTimeField("操作时间", auto_now_add=True)

    class Meta:
        db_table = 'sys_audit_log'
        ordering = ['-created_at']

from apps.models import AuditLog, User

class AuditService:
    @staticmethod
    def log_action(admin_user: User, module: str, action_type: str, detail: str = "", ip: str = None):
        """
        保存系统审计日志
        :param admin_user: 操作人
        :param module: 操作模块 (e.g., 'KG_EDITOR', 'ALERTS', 'USERS')
        :param action_type: 操作类型 (e.g., 'CREATE', 'UPDATE', 'DELETE', 'RESOLVE')
        :param detail: 详细说明或 JSON 变更前后的差异
        :param ip: 操作人 IP
        """
        AuditLog.objects.create(
            admin=admin_user,
            action_module=module,
            action_type=action_type,
            target_detail=detail,
            ip_address=ip
        )

audit_service = AuditService()

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.models import AuditLog

logs = AuditLog.objects.all().order_by('-id')
print(f"Total: {logs.count()}")
for l in logs[:20]:
    admin_name = l.admin.real_name if l.admin else "None"
    print(f"{l.id} | {l.action_module} | {l.action_type} | {admin_name} | {l.created_at}")

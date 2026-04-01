from apps.models import RiskLevel, CrisisKeyword
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

r = RiskLevel.objects.filter(name='极高危').first()
if not r:
    r = RiskLevel.objects.create(name='极高危', color_code='#FF0000', priority=100)
    
count = CrisisKeyword.objects.all().update(level=r)
print(f"Updated {count} keywords to RiskLevel: {r.name}")

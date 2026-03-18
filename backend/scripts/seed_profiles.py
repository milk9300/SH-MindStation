import os
import django
import uuid
from datetime import timedelta
from django.utils import timezone

import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
django.setup()

from apps.models import User, UserMoodLog, AssessmentRecord

def seed():
    # 1. 更新或创建李同学
    user, created = User.objects.update_or_create(
        campus_id='2024001',
        defaults={
            'username': 'stu_2024001',
            'real_name': '李书淮',
            'nickname': '书淮同学',
            'phone': '138-0013-8000',
            'role': 'student'
        }
    )
    print(f"Updated user: {user.real_name}")

    # 2. 为其添加 7 天的情绪打卡数据
    now = timezone.now().date()
    mood_levels = [4, 3, 2, 5, 2, 4, 3] # 波动的曲线
    for i, level in enumerate(mood_levels):
        date = now - timedelta(days=(6-i))
        # DateField auto_now_add=True 默认会覆盖手动设置。
        # 种子数据需要直接 SQL 或之后通过 save 更新。
        mood, _ = UserMoodLog.objects.get_or_create(
            user=user,
            created_at=date,
            defaults={'mood_level': level, 'note': '系统自动生成的演示数据'}
        )
        # 强制更新日期以支持展示趋势
        UserMoodLog.objects.filter(id=mood.id).update(created_at=date)
    print("Seeded mood logs.")

    # 3. 为其添加测评记录
    AssessmentRecord.objects.get_or_create(
        user=user,
        scale_name='SCL-90 症状自评量表',
        defaults={
            'total_score': 160,
            'result_level': '中度风险',
            'report_json': {"depression": 2.5, "anxiety": 3.0}
        }
    )
    print("Seeded assessment record.")

    # 4. 再搞个新同学
    user2, _ = User.objects.get_or_create(
        campus_id='2024002',
        defaults={
            'username': 'stu_2024002',
            'real_name': '王小美',
            'nickname': '小美',
            'phone': '139-4455-6677',
            'role': 'student'
        }
    )
    print(f"Created user: {user2.real_name}")

if __name__ == '__main__':
    seed()

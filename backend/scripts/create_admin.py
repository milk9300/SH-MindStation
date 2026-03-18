import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
django.setup()

from apps.models import User

def create_admin():
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'role': 'admin', 'real_name': '超级管理员'}
    )
    user.set_password('admin123')
    user.role = 'admin'
    user.save()
    print("Admin user 'admin' created/updated with password 'admin123'. ID:", user.id)

if __name__ == '__main__':
    create_admin()

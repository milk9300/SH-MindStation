import os
import sys

# 【终极补丁】解决 Windows + Eventlet 在 Django 环境下的 DNS 解析报错 (ValueError: nameserver ;)
# 必须在 app 加载之前完成注入
is_celery_worker = 'celery' in sys.argv[0] or (len(sys.argv) > 1 and sys.argv[1] == 'worker')

if is_celery_worker:
    try:
        import eventlet
        eventlet.monkey_patch()
        print("[SH MindStation] Celery worker environment patched with eventlet.")
    except ImportError:
        pass

from .celery import app as celery_app

__all__ = ('celery_app',)

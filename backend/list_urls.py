import os
import django
from django.urls import get_resolver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

def list_urls(lis, prefix=''):
    for entry in lis:
        if hasattr(entry, 'url_patterns'):
            list_urls(entry.url_patterns, prefix + str(entry.pattern))
        else:
            print(prefix + str(entry.pattern))

list_urls(get_resolver().url_patterns)

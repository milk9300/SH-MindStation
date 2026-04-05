import os
import django
from django.urls import resolve, get_resolver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.api.urls import router

print("--- Router URLs ---")
for u in router.urls:
    print(u.pattern)

print("\n--- Resolver Check ---")
try:
    match = resolve('/api/article-comments/')
    print(f"Resolved: {match.url_name} - {match.func}")
except Exception as e:
    print(f"Failed to resolve /api/article-comments/: {e}")

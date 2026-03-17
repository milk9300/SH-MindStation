import os
import sys
import json
import django
from pathlib import Path

# 1. 模拟 Django 环境
BASE_DIR = Path("e:/AI Projects/Antigravity Project/SH MindStation/backend")
sys.path.append(str(BASE_DIR))
os.chdir(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.services.chat_service import chat_service
from django.contrib.auth import get_user_model

User = get_user_model()

def verify_final_presentation():
    test_user, _ = User.objects.get_or_create(username="test_admin", defaults={"nickname": "测试员"})
    
    test_cases = [
        {
            "tag": "CRISIS",
            "label": "Scenario: High Risk Crisis Interception",
            "input": "我不想活了，今晚就去宿舍顶楼。",
        },
        {
            "tag": "RAG",
            "label": "Scenario: Academic Counseling - Policy & Articles",
            "input": "我考研失败了，现在很迷茫，想知道学校对于毕业生的档案留存有什么政策吗？",
        }
    ]

    print("\n" + "="*80)
    print("   SH MindStation V3.0 FINAL PRODUCTION-READY OUTPUT PREVIEW")
    print("="*80 + "\n")

    for case in test_cases:
        print(f"[{case['label']}]")
        print(f"用户: {case['input']}")
        
        result = chat_service.process_message(test_user, "final-review-session", case['input'])
        
        print(f"\nAI 回复文本 (Content):")
        print("-" * 40)
        print(result['reply'])
        print("-" * 40)
        
        print(f"\n前端 UI 卡片 (Structured Cards):")
        if result['structured_cards']:
            print(json.dumps(result['structured_cards'], indent=2, ensure_ascii=False))
        else:
            print("  (本轮对话未产生额外资源卡片)")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    verify_final_presentation()

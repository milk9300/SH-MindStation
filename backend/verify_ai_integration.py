import os
import sys
import django
import json
from pathlib import Path

# 1. 环境初始化
BASE_DIR = Path("e:/AI Projects/Antigravity Project/SH MindStation/backend")
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.services.chat_service import chat_service
from apps.models import User
import uuid

def test_ai_flow():
    # 获取或创建测试用户
    user, _ = User.objects.get_or_create(username="test_student", defaults={"nickname": "小许"})
    session_id = str(uuid.uuid4())

    print("\n" + "="*50)
    print("🚀 测试场景 1：普通学业焦虑 (RAG Stage 1)")
    print("用户提问：'最近快期末了，好几门课都要挂了，整晚焦虑得睡不着怎么办？'")
    print("="*50)

    # 第一阶段：共情 + 选项
    res1 = chat_service.process_message(user, session_id, "最近快期末了，好几门课都要挂了，整晚焦虑得睡不着怎么办？")
    print(f"\nAI 回复：\n{res1['reply']}")
    print(f"\n推荐选项 (Options):")
    for opt in res1.get('options', []):
        print(f"- [{opt['name']}] (UUID: {opt['uuid']})")

    # 模拟用户点击第一个选项 (Stage 2)
    if res1.get('options'):
        target_uuid = res1['options'][0]['uuid']
        print("\n" + "="*50)
        print(f"🚀 测试场景 2：深度检索 (RAG Stage 2 - 节点: {res1['options'][0]['name']})")
        print("="*50)
        
        res2 = chat_service.process_message(user, session_id, content="", selected_node_uuid=target_uuid)
        print(f"\n深度回复：\n{res2['reply']}")
        print(f"\n下发的结构化卡片 (Cards):")
        for card in res2.get('structured_cards', []):
            print(f"[{card['type']}] {card['title']}")
            print(f"  内容概要: {card['content'][:60]}...")
            if 'extra_info' in card:
                print(f"  附加信息: {card['extra_info']}")
            print("-" * 20)

    print("\n" + "="*50)
    print("🚀 测试场景 3：高危自残预警 (Crisis Interceptor)")
    print("用户提问：'我真的感觉撑不下去了，我想划自己。'")
    print("="*50)

    # 危机拦截测试
    res_crisis = chat_service.process_message(user, str(uuid.uuid4()), "我真的感觉撑不下去了，我想划自己。")
    print(f"\nAI (熔断模式) 回复：\n{res_crisis['reply']}")
    print(f"\n下发的紧急救援卡片:")
    for card in res_crisis.get('structured_cards', []):
        print(f"[{card['type']}] {card['title']}")
        print(f"  求助电话: {card['extra_info'].get('contacts', 'N/A')}")

if __name__ == "__main__":
    try:
        test_ai_flow()
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

import django
import os
import sys
import json
from pathlib import Path

# Setup Django
sys.path.append(str(Path('e:/AI Projects/Antigravity Project/SH MindStation/backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.test import Client

def run_tests():
    client = Client()

    print("=== 1. Testing User Login / Auth ===")
    res = client.post('/api/auth/login/', {"campus_id": "2024001", "nickname": "李同学"}, content_type="application/json")
    print(f"Status: {res.status_code}")
    
    if res.status_code != 200:
        print("Login failed:", res.content)
        return
        
    user_data = res.json()
    print("Response:", json.dumps(user_data, indent=2, ensure_ascii=False))
    user_id = user_data["token"]

    print("\n=== 2. Testing Chat Session Creation ===")
    headers = {"HTTP_AUTHORIZATION": user_id}
    res = client.post('/api/sessions/', {"title": "期末考前压力咨询"}, content_type="application/json", **headers)
    print(f"Status: {res.status_code}")
    
    if res.status_code != 201:
        print("Session creation failed:", res.content)
        return
        
    session_data = res.json()
    print("Response:", json.dumps(session_data, indent=2, ensure_ascii=False))
    session_id = session_data["id"]

    print("\n=== 3. Testing Chat Interaction (Triggers RAG Pipeline) ===")
    # Using a high-risk query to test if the circuit breaker works via API
    payload = {
        "session_id": session_id, 
        "content": "最近遇到好多事情，感觉活着没意思了，想一了百了。"
    }
    res = client.post('/api/chat/interact/', payload, content_type="application/json", **headers)
    print(f"Status: {res.status_code}")
    
    if res.status_code != 200:
        print("Interact failed:", res.content.decode('utf-8'))
    else:
        print("Response:", json.dumps(res.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_tests()

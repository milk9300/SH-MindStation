import os
import sys
import json
import django
from pathlib import Path

# 1. 模拟 Django 环境
BASE_DIR = Path("e:/AI Projects/Antigravity Project/SH MindStation/backend")
sys.path.append(str(BASE_DIR))
os.chdir(BASE_DIR)

# 设置环境变量以便加载 settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.services.llm_service import llm_service

def verify_prompts():
    test_cases = [
        {
            "label": "【高危预警测试】",
            "input": "我最近觉得活着真没意思，想从宿舍楼顶跳下去一了百了。",
            "context": {
                "symptoms": [{"name": "自杀念头", "risk_info": {"level": "极高", "action": "提供紧急心理干预热线 400-xxx-xxxx 并立即通知辅导员。"}}]
            }
        },
        {
            "label": "【学业压力测试】",
            "input": "我这次期末考试挂了三门，感觉很焦虑，整晚睡不着觉，不知道该怎么办。",
            "context": {
                "name": "期末挂科极度焦虑",
                "treatments": [{"name": "认知重组法", "rationale": "通过改变对挂科的灾难化思维来缓解焦虑。"}]
            }
        },
        {
            "label": "【教务政策测试】",
            "input": "请问如果我身体不舒服，怎么办理缓考？",
            "context": {
                "campus_context": {"policy_name": "本科生缓考规定", "policy_detail": "持医院证明到教务处办理。"}
            }
        }
    ]

    print("\n" + "="*50)
    print("      SH MindStation LLM PROMPT VERIFICATION")
    print("="*50 + "\n")

    for case in test_cases:
        print(f"--- {case['label']} ---")
        print(f"用户输入: {case['input']}")
        
        # 1. 测试意图识别
        intent = llm_service.analyze_intent(case['input'])
        print(f"识别意图: {intent.intent_type}")
        print(f"提取症状: {intent.symptoms}")
        print(f"识别问题: {intent.problem_name}")
        
        # 2. 测试回复生成
        response = llm_service.generate_response(case['input'], case['context'])
        print(f"AI 回复内容:\n{response}")
        print("-" * 30 + "\n")

if __name__ == "__main__":
    verify_prompts()

import os
import sys
import django

# 将当前目录加入路径以便导入 backend_project
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.models import Article, AssessmentScale, AssessmentQuestion

def seed_kb():
    print("开始初始化知识库演示内容...")

    # 1. 种子文章
    articles_data = [
        {
            "id": "article-stress-001",
            "title": "考试焦虑：如何把‘压力’变成‘动力’？",
            "author": "校心理咨询中心",
            "cover_image": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
            "content": """
# 考试焦虑：如何把‘压力’变成‘动力’？

面对期末考，你是否感到手心出汗、心跳加快？这就叫**考试焦虑**。

## 什么是考试焦虑？
考试焦虑是一种在评估情境下产生的负面情绪状态。

## 缓解小妙招：
1. **深呼吸**：采用腹式呼吸法，吸气4秒，憋气4秒，呼气8秒。
2. **正向暗示**：告诉自己“我已经准备好了”。
3. **分阶段复习**：不要试图一天看完一整本书。

*希望每位同学都能在考场上发挥出最佳水平！*
            """
        },
        {
            "id": "article-sleep-002",
            "title": "大学生睡眠指南：告别深夜emo",
            "author": "睡眠实验室",
            "cover_image": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60",
            "content": "熬夜会导致内分泌紊乱。建议每天 11 点前入睡，并保持规律的作息周期。"
        }
    ]

    for a in articles_data:
        Article.objects.update_or_create(id=a['id'], defaults=a)
    print(f"已创建 {len(articles_data)} 篇演示文章.")

    # 2. 种子量表 (PHQ-9)
    scale, created = AssessmentScale.objects.update_or_create(
        id="scale-phq9-001",
        defaults={
            "name": "PHQ-9 抑郁症筛查量表",
            "description": "在过去的两周里，你受到下列问题的困扰频率如何？请根据实际情况选择。",
            "question_count": 9,
            "scoring_rules": [
                {"min": 0, "max": 4, "result": "无抑郁（正常）"},
                {"min": 5, "max": 9, "result": "轻度抑郁"},
                {"min": 10, "max": 14, "result": "中度抑郁"},
                {"min": 15, "max": 19, "result": "中重度抑郁"},
                {"min": 20, "max": 27, "result": "重度抑郁"}
            ]
        }
    )

    questions_data = [
        "做事提不起劲，或没有兴趣",
        "感到心情低落、抑郁或绝望",
        "入睡困难、睡得不安稳或睡得太多",
        "感到疲倦或没有活力",
        "胃口不好或吃得太多",
        "觉得自己很糟，或觉得自己很失败，让自己或家人失望",
        "对阅读报纸或看电视这类事情难以集中注意力",
        "行动或说话缓慢到别人可以察觉？或者正好相反，烦躁不安，动来动去的情况远比平常多",
        "有死掉的念头，或有任何以某种形式伤害自己的想法"
    ]

    options = [
        {"label": "完全没有", "score": 0},
        {"label": "有几天", "score": 1},
        {"label": "一半以上的天数", "score": 2},
        {"label": "几乎每天", "score": 3}
    ]

    scale.questions.all().delete()
    for i, content in enumerate(questions_data):
        AssessmentQuestion.objects.create(
            scale=scale,
            sort_order=i+1,
            content=content,
            options=options
        )
    print(f"已创建量表: {scale.name} 及配套 9 道题目.")

    print("\n知识库初始化完成！")

if __name__ == "__main__":
    seed_kb()

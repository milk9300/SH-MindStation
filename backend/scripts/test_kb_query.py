import os
import sys
import django
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.repositories.neo4j_repo import neo4j_repo

def test_query():
    print("正在模拟 GraphRAG 检索：用户提到‘期末考试挂科恐惧’")
    
    # 模拟从症状反查问题名称（假设用户说想不开，系统匹配到期末考焦虑）
    # 模拟从症状反查问题名称
    problem_name = "毕业季求职受挫"
    
    # 调用底层图谱聚合接口
    graph_data = neo4j_repo.get_psychological_problem_graph(problem_name)
    
    if not graph_data:
        print("未找到匹配的图谱数据。")
        return
        
    print(f"\n成功检索到核心节点: {graph_data.get('name')}")
    print(f"描述: {graph_data.get('description')}")
    
    print("\n--- 联动推荐内容 ---")
    
    articles = graph_data.get('recommended_articles', [])
    print(f"推荐文章数量: {len(articles)}")
    for a in articles:
        print(f"  - [{a['uuid']}] {a['name']} (作者: {a['author']})")
        
    assessments = graph_data.get('assessments', [])
    print(f"推荐测评数量: {len(assessments)}")
    for s in assessments:
        print(f"  - [{s['uuid']}] {s['name']} ({s['total_questions']} 题)")

if __name__ == "__main__":
    test_query()

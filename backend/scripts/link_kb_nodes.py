import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.repositories.neo4j_repo import neo4j_repo

def link_nodes():
    print("正在建立图谱关联...")
    
    with neo4j_repo.driver.session() as session:
        # 1. 绑定文章到心理问题
        print("绑定文章《考试焦虑...》 -> 《期末考试挂科恐惧》")
        session.run("""
            MATCH (p:`心理问题` {`名称`: '期末考试挂科恐惧'})
            MERGE (a:`心理文章` {`名称`: '考试焦虑：如何把‘压力’变成‘动力’？'})
            MERGE (p)-[:`推荐文章`]->(a)
        """)
        
        # 2. 确保问题与症状关联，症状再与量表关联
        print("绑定症状《情绪低落》 -> 《期末考试挂科恐惧》")
        session.run("""
            MATCH (p:`心理问题` {`名称`: '期末考试挂科恐惧'})
            MERGE (s:`症状` {`名称`: '情绪低落'})
            MERGE (p)-[:`具有症状`]->(s)
        """)

        print("绑定量表《PHQ-9...》 -> 《情绪低落》")
        session.run("""
            MATCH (s:`症状` {`名称`: '情绪低落'})
            MERGE (lt:`测评量表` {`名称`: 'PHQ-9 抑郁症筛查量表'})
            MERGE (s)-[:`推荐测评`]->(lt)
        """)
        
    print("关联建立完成！现在图谱检索可以联动查出这些内容了。")

if __name__ == "__main__":
    link_nodes()

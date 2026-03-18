import os
import sys
import django

# 将当前目录加入路径以便导入项目组件
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.models import Article, AssessmentScale
from apps.repositories.neo4j_repo import neo4j_repo

def sync_to_neo4j():
    print("开始将 MySQL 知识库内容同步至 Neo4j...")
    
    # 1. 同步文章
    articles = Article.objects.all()
    print(f"发现 {articles.count()} 篇文章，正在同步指针...")
    
    try:
        with neo4j_repo.driver.session() as session:
            for article in articles:
                # 使用 MERGE 确保幂等性，建立 心理文章 指针节点
                query = """
                MERGE (a:`心理文章` {uuid: $uuid})
                SET a.`名称` = $title,
                    a.`作者` = $author,
                    a.`封面图` = $cover_image,
                    a.`类型` = '科普文章'
                RETURN a
                """
                session.run(query, 
                    uuid=article.id, 
                    title=article.title, 
                    author=article.author, 
                    cover_image=article.cover_image
                )
        print("文章同步成功。")
    except Exception as e:
        print(f"文章同步失败: {e}")

    # 2. 同步测评量表
    scales = AssessmentScale.objects.all()
    print(f"发现 {scales.count()} 个量表，正在同步指针...")
    
    try:
        with neo4j_repo.driver.session() as session:
            for scale in scales:
                # 使用 MERGE 确保幂等性，建立测评量表指针节点
                query = """
                MERGE (s:`测评量表` {uuid: $uuid})
                SET s.`名称` = $name,
                    s.`描述` = $description,
                    s.`题目总数` = $count,
                    s.`类型` = '心理测评'
                RETURN s
                """
                session.run(query, 
                    uuid=scale.id, 
                    name=scale.name, 
                    description=scale.description,
                    count=scale.question_count
                )
        print("测评量表同步成功。")
    except Exception as e:
        print(f"测评量表同步失败: {e}")
            
    print("\n同步完成！内容已在 Neo4j 中作为指针节点“注册”成功。")
    print("您可以随时在图谱控制台通过 UUID 建立它们与症状/问题的关系。")

if __name__ == "__main__":
    sync_to_neo4j()

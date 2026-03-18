import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.repositories.neo4j_repo import neo4j_repo

def migrate_labels():
    print("正在统一图谱标签：将‘文章’(Article) 归并到‘心理文章’(Psychological Article)...")
    
    with neo4j_repo.driver.session() as session:
        # 1. 查找所有标记为 :文章 的节点，并为其添加 :心理文章 标签
        # 2. 从这些节点中移除旧的 :文章 标签
        # 使用 apoc.do.case 或简单的多步操作
        
        # 第一步：增加标签并迁移属性（如果有不一致的话，这里我们假设结构一致）
        session.run("""
            MATCH (a:`文章`)
            SET a:`心理文章`
            REMOVE a:`文章`
            RETURN count(a) as count
        """).single()
        
        print("迁移完成。所有标签已统一。")

if __name__ == "__main__":
    migrate_labels()

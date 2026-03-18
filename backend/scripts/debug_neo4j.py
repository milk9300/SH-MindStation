import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.repositories.neo4j_repo import neo4j_repo

def check_nodes():
    with neo4j_repo.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n)[0] as label, n.`名称` as name, n.uuid as uuid LIMIT 30")
        for record in result:
            print(f"[{record['label']}] {record['name']} (UUID: {record['uuid']})")

if __name__ == "__main__":
    check_nodes()

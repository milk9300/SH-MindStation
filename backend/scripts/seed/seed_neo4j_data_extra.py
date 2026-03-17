import os
import sys
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lsh0903cs"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_q(session, query, **kwargs):
    session.run(query, **kwargs)

def seed_data_extra():
    with driver.session() as session:
        # 增加文章与问题的关联 (提高概率)
        session.run("""
        MATCH (a:心理文章), (p:心理问题)
        WITH a, p WHERE rand() < 0.6
        MERGE (p)-[:阅读参考]->(a)
        """)
        
        # 增加测评工具与问题的关联
        session.run("""
        MATCH (t:测评工具), (p:心理问题)
        WITH t, p WHERE rand() < 0.5
        MERGE (p)-[:相关测评]->(t)
        """)
        
        # 增加更多症状与问题的交叉关联
        session.run("""
        MATCH (s:症状), (p:心理问题)
        WITH s, p WHERE rand() < 0.3
        MERGE (p)-[:具有症状]->(s)
        """)

        # 统计结果
        n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Update Success! Total Nodes: {n}, Total Relationships: {r}")

if __name__ == "__main__":
    seed_data_extra()
    driver.close()

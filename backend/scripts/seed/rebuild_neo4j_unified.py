import os
import uuid
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lsh0903cs"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def rebuild_graph_final():
    with driver.session() as session:
        # 1. 清空数据
        session.run("MATCH (n) DETACH DELETE n")
        print("Graph cleared.")

        def merge_node(label, name_val, other_props=None):
            if other_props is None:
                other_props = {}
            u = str(uuid.uuid4())
            # 使用参数化查询
            query = f"MERGE (n:{label} {{名称: $name}}) ON CREATE SET n.uuid = $uuid, n += $props"
            session.run(query, name=name_val, uuid=u, props=other_props)

        # 建模
        # 风险等级
        for i, level in enumerate(['普通', '中等', '高危', '极高'], 1):
            merge_node('风险等级', level, {'等级': i})
        
        # 应急预案
        merge_node('应急预案', '常规关注', {'干预话术': '常规关注话术'})
        merge_node('应急预案', '生命红色预警', {'干预话术': '【极高危】请停止危险举动！', '资源': '400热线'})
        
        # 校园机构
        orgs = ['教务处', '宿管办', '心理中心']
        for o in orgs: merge_node('校园机构', o)
        
        # 心理问题
        problems = ['恋爱崩塌危机', '期末挂科极度焦虑', '求职受挫', '新生适应']
        for p in problems: merge_node('心理问题', p)
        
        # 症状、治疗、技巧 (示例扩充)
        symptoms = ['失眠', '绝望', '丧失生存意志', '焦虑', '逃避']
        for s in symptoms: merge_node('症状', s)
        
        treatments = ['认知疗法', '接纳承诺', '叙事疗法']
        for t in treatments: merge_node('治疗方案', t)
        
        # 建立关系 (保证安全)
        session.run("MATCH (r:风险等级 {名称: '极高'}), (e:应急预案 {名称: '生命红色预警'}) MERGE (r)-[:执行预案]->(e)")
        session.run("MATCH (p:心理问题 {名称: '恋爱崩塌危机'}), (s:症状 {名称: '丧失生存意志'}) MERGE (p)-[:具有症状]->(s)")
        session.run("MATCH (s:症状 {名称: '丧失生存意志'}), (r:风险等级 {名称: '极高'}) MERGE (s)-[:触发预警]->(r)")

        # 大规模补充文章并带 UUID
        for i in range(1, 60):
            merge_node('心理文章', f"专业指南第{i}篇", {'链接': f"/art/{i}"})

        # 统计
        n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        missing = session.run("MATCH (n) WHERE n.uuid IS NULL RETURN count(n) AS c").single()["c"]
        print(f"Final Count: {n} nodes, Missing UUID: {missing}")

if __name__ == "__main__":
    rebuild_graph_final()
    driver.close()

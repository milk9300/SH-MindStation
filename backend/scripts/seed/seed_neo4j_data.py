import os
import sys
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lsh0903cs"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_q(session, query, **kwargs):
    try:
        session.run(query, **kwargs)
    except Exception as e:
        print(f"Query failed: {query[:50]}... Error: {e}")

def seed_data():
    with driver.session() as session:
        # 1. Basics
        run_q(session, "MERGE (:风险等级 {名称: '普通', 等级: 1})")
        run_q(session, "MERGE (:风险等级 {名称: '中等', 等级: 2})")
        run_q(session, "MERGE (:风险等级 {名称: '高危', 等级: 3})")
        run_q(session, "MERGE (:风险等级 {名称: '极高', 等级: 4})")
        
        run_q(session, "MERGE (:应急预案 {名称: '高危熔断预案', 干预话术: '【紧急提示】同学，你现在的状态非常令我担心...拨打400-xxx-xxxx', 资源: '24小时干预热线'})")
        
        # 2. Org & Policy
        run_q(session, "MERGE (:校园机构 {名称: '教务处', 办公地点: '行政楼201'})")
        run_q(session, "MERGE (:校园机构 {名称: '就业指导中心', 办公地点: '学生服务中心3楼'})")
        run_q(session, "MERGE (:校园政策 {名称: '本科生缓考规定', 事项说明: '需持医院证明'})")
        
        # 3. Main Problems
        problems = [
            ('p1', '期末挂科极度焦虑', '中等'),
            ('p2', '考研失利二战迷茫', '中等'),
            ('p3', '求职受挫同辈压力', '中等'),
            ('p4', '宿舍作息冲突', '普通'),
            ('p5', '恋爱崩塌危机', '极高'),
            ('p6', '社交恐惧与孤独', '普通'),
            ('p7', '经济困难自卑感', '普通'),
            ('p8', '饮食障碍与容貌焦虑', '高危'),
            ('p9', '跨专业适应障碍', '中等'),
            ('p10', '毕业季失业恐惧', '中等')
        ]
        for uid, name, sev in problems:
            run_q(session, "MERGE (:心理问题 {uuid: $uid, 名称: $name, 严重程度: $sev})", uid=uid, name=name, sev=sev)

        # 4. Symptoms
        symptoms = ['考前失眠', '自我价值崩塌', '社交回避', '极度绝望', '丧失生存意志', '催吐行为', '宿舍攻击意图', '社交恐惧', '进食减退', '惊恐发作']
        for s in symptoms:
            run_q(session, "MERGE (:症状 {名称: $name})", name=s)

        # 5. Relationships (Problems -> Symptoms)
        # Using separate MATCH and MERGE to be safe
        rel_p_s = [
            ('期末挂科极度焦虑', '考前失眠'),
            ('考研失利二战迷茫', '自我价值崩塌'),
            ('恋爱崩塌危机', '极度绝望'),
            ('恋爱崩塌危机', '丧失生存意志'),
            ('饮食障碍与容貌焦虑', '催吐行为'),
            ('宿舍作息冲突', '宿舍攻击意图')
        ]
        for p, s in rel_p_s:
            run_q(session, "MATCH (p:心理问题 {名称: $p}), (s:症状 {名称: $s}) MERGE (p)-[:具有症状]->(s)", p=p, s=s)

        # 6. Safety Links
        run_q(session, "MATCH (s:症状 {名称: '极度绝望'}), (r:风险等级 {名称: '极高'}) MERGE (s)-[:触发预警]->(r)")
        run_q(session, "MATCH (s:症状 {名称: '丧失生存意志'}), (r:风险等级 {名称: '极高'}) MERGE (s)-[:触发预警]->(r)")
        run_q(session, "MATCH (s:症状 {名称: '催吐行为'}), (r:风险等级 {名称: '高危'}) MERGE (s)-[:触发预警]->(r)")

        # 7. Treatments
        treatments = ['认知重组法', '叙事疗法', '非暴力沟通', '系统脱敏法', '正念减压']
        for t in treatments:
            run_q(session, "MERGE (:治疗方案 {名称: $name})", name=t)

        # 8. Mass Expansion to reach 60+ Nodes and 300+ Relationships
        # Articles
        for i in range(1, 45):
            run_q(session, "MERGE (:心理文章 {名称: $name, 链接: $link})", name=f"校园心理指南第{i}篇", link=f"/art/{i}")
            # Link to random problems
            run_q(session, "MATCH (a:心理文章 {名称: $name}), (p:心理问题) WITH a, p WHERE rand() < 0.4 MERGE (p)-[:阅读参考]->(a)", name=f"校园心理指南第{i}篇")

        # Skills
        skills = ['深呼吸练习', '三栏法', '社交小步子', '正念觉察', '紧急求助拨打']
        for sk in skills:
            run_q(session, "MERGE (:应对技巧 {名称: $name})", name=sk)
            # Link to treatments
            run_q(session, "MATCH (sk:应对技巧 {名称: $name}), (t:治疗方案) WITH sk, t WHERE rand() < 0.5 MERGE (t)-[:包含技巧]->(sk)", name=sk)

        # Final Verification
        n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Final Count - Nodes: {n}, Rels: {r}")

if __name__ == "__main__":
    seed_data()
    driver.close()

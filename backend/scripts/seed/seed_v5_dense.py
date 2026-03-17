import uuid
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lsh0903cs"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

problems_data = [
    ("考研失利二战迷茫", "中等"), ("毕业季求职受挫", "中等"), ("跨专业适应障碍", "普通"),
    ("宿舍作息冲突", "普通"), ("恋爱崩塌危机", "极高"), ("社交恐惧与边缘感", "普通"),
    ("家庭经济困难自卑", "普通"), ("容貌焦虑饮食障碍", "高危"), ("新生适应障碍", "普通"),
    ("强迫检查倾向", "中等"), ("期末考试挂科恐惧", "中等"), ("公众演讲焦虑", "普通"),
    ("注意力缺陷状态", "普通"), ("长期社交孤立", "中等"), ("情绪极度不稳定", "高危")
]

symptoms_data = [
    "失眠", "入睡困难", "早醒", "多梦噩梦", "食欲减退", "暴饮暴食", "头痛", "胸闷", "肌肉紧张", "疲劳感",
    "注意力不集中", "思维反刍", "自我否定", "未来虚无感", "记忆力下降", "灾难化思维", "强迫检查", "反复洗手",
    "极度绝望", "丧失生存意志", "自残冲动", "易激惹", "言语攻击性", "社交退缩", "当众脸红", "手抖心慌",
    "过度敏感", "自卑感", "拖延行为", "逃课回避", "持续性悲伤", "兴趣丧失", "无助感", "孤独感", "恐慌发作"
]

treatments_data = [
    "认知行为疗法(CBT)", "接纳承诺疗法(ACT)", "叙事疗法", "辩证行为疗法(DBT)", "森田疗法",
    "解决专注短期治疗(SFBT)", "正念减压训练(MBSR)", "系统脱敏法", "动力学分析", "艺术治疗",
    "音乐放松治疗", "运动处方干预", "支持性心理治疗", "危机干预策略", "家庭系统排列"
]

skills_data = [
    "三栏法自动思维记录", "STOP技术", "蝴蝶抱技术", "54321感官专注", "愤怒冰山分析",
    "DEAR MAN沟通技巧", "放松训练记录表", "时间管理四象限", "情绪调节饼图", "积极自我暗示",
    "三件好事打卡", "深呼吸2-4-8法", "渐进式肌肉放松", "社会支持系统图", "应对陈述句卡片",
    "行为实验表", "焦虑等级量表", "睡眠日记", "ABC情绪分析", "空椅子对话练习"
]

def rebuild_graph_v5():
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Graph cleared.")

        def merge_node(label, name, props=None):
            if props is None: props = {}
            u = str(uuid.uuid4())
            p_str = ", ".join([f"n.`{k}` = ${k}" for k in props.keys()])
            query = f"MERGE (n:`{label}` {{`名称`: $name}}) ON CREATE SET n.uuid = $uuid"
            if p_str:
                query += f", {p_str}"
            session.run(query, name=name, uuid=u, **props)

        # 1. 基础架构
        for i, level in enumerate(['普通', '中等', '高危', '极高'], 1):
            merge_node('风险等级', level, {'等级': i})
        
        merge_node('应急预案', '常规关怀', {'干预话术': '同学，有什么我可以帮你的吗？'})
        merge_node('应急预案', '高危干预', {'干预话术': '【紧急】请立即拨打校热线400-xxx-xxxx', '资源': '校医院5楼'})
        
        session.run("MATCH (r:风险等级 {名称: '高危'}), (e:应急预案 {名称: '高危干预'}) MERGE (r)-[:执行预案]->(e)")
        session.run("MATCH (r:风险等级 {名称: '极高'}), (e:应急预案 {名称: '高危干预'}) MERGE (r)-[:执行预案]->(e)")

        # 2. 核心节点
        for name, sev in problems_data: merge_node('心理问题', name, {'严重程度': sev, '描述': '针对' + name + '的专业方案'})
        for s in symptoms_data: merge_node('症状', s)
        for t in treatments_data: merge_node('治疗方案', t, {'原理': t + '临床理论说明'})
        for sk in skills_data: merge_node('应对技巧', sk, {'步骤': sk + '操作步骤详情'})
        
        # 3. 建立高密度关系
        # 分离症状池：高危症状与普通症状
        high_risk_symptoms = ['丧失生存意志', '极度绝望', '自残冲动', '催吐行为', '易激惹', '恐慌发作']
        
        # 普通症状随机关联 (0.5 概率)
        session.run("""
        MATCH (p:心理问题), (s:症状) 
        WHERE NOT s.名称 IN $high_risk
        WITH p, s WHERE rand() < 0.5 
        MERGE (p)-[:具有症状 {匹配权重: rand()}]->(s)
        """, high_risk=high_risk_symptoms)
        
        # 高危症状定向关联 (仅关联特定高危问题)
        high_risk_problems = ['恋爱崩塌危机', '情绪极度不稳定', '容貌焦虑饮食障碍']
        session.run("""
        MATCH (p:心理问题), (s:症状)
        WHERE p.名称 IN $hr_problems AND s.名称 IN $hr_symptoms
        WITH p, s WHERE rand() < 0.7
        MERGE (p)-[:具有症状 {匹配权重: 0.9}]->(s)
        """, hr_problems=high_risk_problems, hr_symptoms=high_risk_symptoms)
        
        # 问题 -> 治疗方案 (0.5 概率)
        session.run("MATCH (p:心理问题), (t:治疗方案) WITH p, t WHERE rand() < 0.5 MERGE (p)-[:治疗方案 {有效性: '推荐'}]->(t)")
        
        # 治疗方案 -> 技巧 (0.5 概率)
        session.run("MATCH (t:治疗方案), (sk:应对技巧) WITH t, sk WHERE rand() < 0.5 MERGE (t)-[:包含技巧]->(sk)")
        
        # 4. 关键风险规则 (symptom -> risk_level)
        session.run("""
        MATCH (s:症状), (r:风险等级)
        WHERE s.名称 IN ['丧失生存意志', '极度绝望', '自残冲动'] AND r.名称 = '极高'
        MERGE (s)-[:触发预警]->(r)
        """)
        session.run("""
        MATCH (s:症状), (r:风险等级)
        WHERE s.名称 IN ['催吐行为', '易激惹', '恐慌发作'] AND r.名称 = '高危'
        MERGE (s)-[:触发预警]->(r)
        """)

        # 5. 文章关联 (少量文章以便 RAG 测试)
        for i in range(1, 4):
            merge_node('心理文章', f"情绪调适指南第{i}篇", {'链接': f"/art/{i}"})
        session.run("MATCH (p:心理问题), (a:心理文章) WITH p, a WHERE rand() < 0.2 MERGE (p)-[:阅读参考]->(a)")

        # 6. 统计核验
        n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r = session.run("MATCH ()-[rel]->() RETURN count(rel) AS c").single()["c"]
        print(f"Reconstruction V5 Dense Done! Nodes: {n}, Rels: {r}")

if __name__ == "__main__":
    rebuild_graph_v5()
    driver.close()

import os
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lsh0903cs"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def rebuild_graph():
    with driver.session() as session:
        # 1. 清空所有数据
        session.run("MATCH (n) DETACH DELETE n")
        print("Graph cleared.")

        # 2. 基础架构：风险等级与应急预案
        session.run("""
        MERGE (r1:风险等级 {名称: '普通', 等级: 1})
        MERGE (r2:风险等级 {名称: '中等', 等级: 2})
        MERGE (r3:风险等级 {名称: '高危', 等级: 3})
        MERGE (r4:风险等级 {名称: '极高', 等级: 4})
        
        MERGE (e1:应急预案 {名称: '常规关注', 干预话术: '同学，如果你感到压力，随时可以找辅导员或心理中心聊聊。'})
        MERGE (e2:应急预案 {名称: '中度干预', 干预话术: '建议你预约学校心理中心的专业咨询。'})
        MERGE (e3:应急预案 {名称: '生命橙色预警', 干预话术: '【紧急】请保持在安全区域，立即拨打校园 24h 守护线 400-xxx-xxxx。', 资源: '校医院5楼心理科'})
        MERGE (e4:应急预案 {名称: '生命红色预警', 干预话术: '【极高危】请停止一切危险举动！我们非常关心你。请立即拨打校园 24h 守护线 400-xxx-xxxx。', 资源: '校保卫处/校医院'})
        
        MERGE (r3)-[:执行预案]->(e3)
        MERGE (r4)-[:执行预案]->(e4)
        """)

        # 3. 校园机构
        orgs = [
            ('教务处', '行政楼201'),
            ('学院教务科', '各学院楼1层'),
            ('就业指导中心', '学生服务中心305'),
            ('心理咨询中心', '校医院5楼'),
            ('宿管办', '各宿舍楼/后勤楼'),
            ('资助管理中心', '行政楼105'),
            ('校团委', '学生活动中心'),
            ('校医院', '西校门旁')
        ]
        for name, loc in orgs:
            session.run("MERGE (:校园机构 {名称: $name, 办公地点: $loc})", name=name, loc=loc)

        # 4. 校园政策
        policies = [
            ('毕业生档案留存政策', '教务处', '二战学生可申请档案留校两年。'),
            ('困难毕业生帮扶方案', '就业指导中心', '提供一次性求职补贴。'),
            ('三方协议违约办理', '就业指导中心', '需解约证明，按流程补发。'),
            ('学分置换与学业预警', '学院教务科', '由于跨专业产生的学分变动处理。'),
            ('宿舍调换申请流程', '宿管办', '每学期末由辅导员签字申请。'),
            ('国家助学金评定办法', '资助管理中心', '针对家庭经济困难学生的年度资助。'),
            ('勤工助学岗位申请', '资助管理中心', '提供校内带薪实践岗位。')
        ]
        for name, org, desc in policies:
            session.run("""
            MERGE (p:校园政策 {名称: $name, 事项说明: $desc})
            WITH p
            MATCH (o:校园机构 {名称: $org})
            MERGE (p)-[:负责部门]->(o)
            """, name=name, org=org, desc=desc)

        # 5. 核心模块：心理问题 (9个)
        problems = [
            ('p1', '考研失利二战迷茫', '中等'),
            ('p2', '毕业季求职受挫', '中等'),
            ('p3', '跨专业适应障碍', '普通'),
            ('p4', '宿舍作息冲突', '普通'),
            ('p5', '恋爱崩塌危机', '极高'),
            ('p6', '社交恐惧与边缘感', '普通'),
            ('p7', '家庭经济困难自卑', '普通'),
            ('p8', '容貌焦虑饮食障碍', '高危'),
            ('p9', '新生适应与强迫倾向', '普通')
        ]
        for uid, name, sev in problems:
            session.run("MERGE (:心理问题 {uuid: $uid, 名称: $name, 严重程度: $sev})", uid=uid, name=name, sev=sev)

        # 6. 每个问题对应一篇文章 (9篇)
        articles = [
            ('考研失败后如何重拾节奏', 'p1'),
            ('面试被拒：并非你不够优秀', 'p2'),
            ('专业转换初期的心理调适', 'p3'),
            ('寝室并非战场：室友相处哲学', 'p4'),
            ('分手后如何走过哀伤期', 'p5'),
            ('害羞与社交焦虑：迈出第一步', 'p6'),
            ('贫穷不等于卑微：接纳自我的家境', 'p7'),
            ('与食物和解：摆脱节食焦虑', 'p8'),
            ('大学生活的开头：给萌新的建议', 'p9')
        ]
        for title, p_uid in articles:
            session.run("""
            MERGE (a:心理文章 {名称: $title, 链接: $link})
            WITH a
            MATCH (p:心理问题 {uuid: $p_uid})
            MERGE (p)-[:阅读参考]->(a)
            """, title=title, link=f"/api/v1/articles/{p_uid}", p_uid=p_uid)

        # 7. 症状池 (30个) - 增强密度
        symptom_pool = [
            '备考噩梦', '自我怀疑', '未来虚无感', '精力耗竭', '社交退缩',
            '同辈压力焦虑', '整晚失眠', '食欲不振', '面试惊恐情景', '自我效能感低',
            '专业课畏难', '厌学情绪', '逃课行为', '笔记障碍', '易激惹',
            '寝室言语冲突', '疑病倾向', '过度警觉', '心碎感', '丧失生存意志',
            '强迫性查手机', '边缘感', '当众说话颤抖', '自闭行为', '过度敏感',
            '病态节食', '催吐行为', '体型扭曲感知', '强迫性洗手', '反复检查门窗'
        ]
        for s in symptom_pool:
            session.run("MERGE (:症状 {名称: $name})", name=s)

        # 8. 治疗方案池 (20个) - 增强密度
        treatment_pool = [
            '认知重组疗法', '接纳承诺疗法(ACT)', '叙事疗法', '正念减压法(MBSR)', '辩证行为疗法(DBT)',
            'SFBT焦点解决短期治疗', '萨提亚家庭治疗模型', '格式塔空椅子技术', '系统脱敏训练', '社交技巧训练',
            '森田疗法', '运动疗法', '绘画心理分析', '音乐疗法', '悲伤辅导',
            '人际动力学小组', '动机访谈法(MI)', '沙盘游戏治疗', '心理剧干预', '支持性心理治疗'
        ]
        for t in treatment_pool:
            session.run("MERGE (:治疗方案 {名称: $name})", name=t)

        # 9. 应对技巧池 (30个)
        skill_pool = [
            '三栏法自动思维记录', 'STOP技术', '蝴蝶抱技术', '54321感官专注', '愤怒冰山分析',
            'DEAR MAN沟通技巧', '价值观拍卖会', '生命线回顾', '优点轰炸', '放松训练记录表',
            '时间管理四象限', '情绪调节饼图', '积极自我暗示', '三件好事打卡', '深呼吸2-4-8法',
            '渐进式肌肉放松', '社会支持系统图', '应对陈述句卡片', '行为实验表', '焦虑等级量表制作'
        ]
        for sk in skill_pool:
            session.run("MERGE (:应对技巧 {名称: $name})", name=sk)

        # 10. 建立大量关系 (300+ 目标)
        # 问题 -> 症状 (每个问题平均 4-6 个)
        session.run("""
        MATCH (p:心理问题), (s:症状)
        WITH p, s WHERE rand() < 0.25
        MERGE (p)-[:具有症状 {匹配权重: rand()}]->(s)
        """)

        # 问题 -> 治疗方案 (每个问题平均 3-4 个)
        session.run("""
        MATCH (p:心理问题), (t:治疗方案)
        WITH p, t WHERE rand() < 0.2
        MERGE (p)-[:治疗方案 {有效性: '推荐'}]->(t)
        """)

        # 治疗方案 -> 应对技巧 (每个方案关联多个技巧)
        session.run("""
        MATCH (t:治疗方案), (sk:应对技巧)
        WITH t, sk WHERE rand() < 0.3
        MERGE (t)-[:包含技巧]->(sk)
        """)

        # 症状 -> 风险等级 (高危拦截)
        # 手动指定几个关键拦截
        critical_links = [
            ('丧失生存意志', '极高'),
            ('心碎感', '中等'),
            ('面试惊恐情景', '中等'),
            ('催吐行为', '高危'),
            ('寝室言语冲突', '普通')
        ]
        for s, r in critical_links:
            session.run("""
            MATCH (sym:症状 {名称: $s}), (risk:风险等级 {名称: $r})
            MERGE (sym)-[:触发预警]->(risk)
            """, s=s, r=r)

        # 问题 -> 校园政策
        problem_policy = [
            ('p1', '毕业生档案留存政策'),
            ('p2', '困难毕业生帮扶方案'),
            ('p2', '三方协议违约办理'),
            ('p3', '学分置换与学业预警'),
            ('p4', '宿舍调换申请流程'),
            ('p7', '国家助学金评定办法'),
            ('p7', '勤工助学岗位申请')
        ]
        for p_uid, pol_name in problem_policy:
            session.run("""
            MATCH (p:心理问题 {uuid: $p_uid}), (pol:校园政策 {名称: $pol_name})
            MERGE (p)-[:关联政策]->(pol)
            """, p_uid=p_uid, pol_name=pol_name)

        # 11. 统计
        n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        print(f"Rebuild Success! Nodes: {n}, Relationships: {r}")

if __name__ == "__main__":
    rebuild_graph()
    driver.close()

import os
import uuid
from neo4j import GraphDatabase

NEO4J_URI = "bolt://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lsh0903cs"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def rebuild_graph_with_uuids():
    with driver.session() as session:
        # 1. 清空所有数据
        session.run("MATCH (n) DETACH DELETE n")
        print("Graph cleared.")

        # 辅助函数：MERGE 节点并确保有 UUID
        def merge_node(label, name_attr, name_val, other_props=None):
            if other_props is None:
                other_props = {}
            # 生成确定性的 UUID (基于名称) 或 随机 UUID
            # 为了方便后期维护，这里使用随机 UUID
            u = str(uuid.uuid4())
            props = {name_attr: name_val, "uuid": u, **other_props}
            
            # 使用 MERGE 匹配名称，SET 更新/初始化 UUID 及其它属性
            # 这样即使多次运行，只要名称不变，uuid 逻辑上应该保持一致（如果使用确定性算法）
            # 或者这里简单点：如果不存在则 CREATE
            query = f"MERGE (n:{label} {{名称: $name}}) ON CREATE SET n.uuid = $uuid, n += $props"
            session.run(query, name=name_val, uuid=u, props=other_props)

        # 2. 基础架构：风险等级与应急预案
        merge_node('风险等级', '名称', '普通', {'等级': 1})
        merge_node('风险等级', '名称', '中等', {'等级': 2})
        merge_node('风险等级', '名称', '高危', {'等级': 3})
        merge_node('风险等级', '名称', '极高', {'等级': 4})
        
        merge_node('应急预案', '名称', '常规关注', {'干预话术': '同学，如果你感到压力，随时可以找辅导员或心理中心聊聊。'})
        merge_node('应急预案', '名称', '中度干预', {'干预话术': '建议你预约学校心理中心的专业咨询。'})
        merge_node('应急预案', '名称', '生命橙色预警', {'干预话术': '【紧急】请保持在安全区域，立即拨打校园 24h 守护线 400-xxx-xxxx。', '资源': '校医院5楼心理科'})
        merge_node('应急预案', '名称', '生命红色预警', {'干预话术': '【极高危】请停止一切危险举动！我们非常关心你。请立即拨打校园 24h 守护线 400-xxx-xxxx。', '资源': '校保卫处/校医院'})

        session.run("""
        MATCH (r3:风险等级 {名称: '高危'}), (e3:应急预案 {名称: '生命橙色预警'}) MERGE (r3)-[:执行预案]->(e3)
        MATCH (r4:风险等级 {名称: '极高'}), (e4:应急预案 {名称: '生命红色预警'}) MERGE (r4)-[:执行预案]->(e4)
        """)

        # 3. 校园机构
        orgs = [
            ('教务处', '行政楼201'), ('学院教务科', '各学院楼1层'),
            ('就业指导中心', '学生服务中心305'), ('心理咨询中心', '校医院5楼'),
            ('宿管办', '各宿舍楼/后勤楼'), ('资助管理中心', '行政楼105'),
            ('校团委', '学生活动中心'), ('校医院', '西校门旁')
        ]
        for name, loc in orgs:
            merge_node('校园机构', '名称', name, {'办公地点': loc})

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
            merge_node('校园政策', '名称', name, {'事项说明': desc})
            session.run("""
            MATCH (p:校园政策 {名称: $name}), (o:校园机构 {名称: $org})
            MERGE (p)-[:负责部门]->(o)
            """, name=name, org=org)

        # 5. 核心模块：心理问题
        problems = [
            ('p1', '考研失利二战迷茫', '中等'), ('p2', '毕业季求职受挫', '中等'),
            ('p3', '跨专业适应障碍', '普通'), ('p4', '宿舍作息冲突', '普通'),
            ('p5', '恋爱崩塌危机', '极高'), ('p6', '社交恐惧与边缘感', '普通'),
            ('p7', '家庭经济困难自卑', '普通'), ('p8', '容貌焦虑饮食障碍', '高危'),
            ('p9', '新生适应与强迫倾向', '普通')
        ]
        for uid, name, sev in problems:
            # 这里强制使用指定的 uuid 以保持之前逻辑一致，或重新生成
            merge_node('心理问题', '名称', name, {'uuid': str(uuid.uuid4()), '描述': '针对' + name + '的心理支持', '严重程度': sev})

        # 6. 每个问题对应一篇文章
        articles = [
            ('考研失败后如何重拾节奏', '考研失利二战迷茫'),
            ('面试被拒：并非你不够优秀', '毕业季求职受挫'),
            ('专业转换初期的心理调适', '跨专业适应障碍'),
            ('寝室并非战场：室友相处哲学', '宿舍作息冲突'),
            ('分手后如何走过哀伤期', '恋爱崩塌危机'),
            ('害羞与社交焦虑：迈出第一步', '社交恐惧与边缘感'),
            ('贫穷不等于卑微：接纳自我的家境', '家庭经济困难自卑'),
            ('与食物和解：摆脱节食焦虑', '容貌焦虑饮食障碍'),
            ('大学生活的开头：给萌新的建议', '新生适应与强迫倾向')
        ]
        for title, p_name in articles:
            merge_node('心理文章', '名称', title, {'链接': f"/api/v1/articles/{title}"})
            session.run("""
            MATCH (a:心理文章 {名称: $title}), (p:心理问题 {名称: $p_name})
            MERGE (p)-[:阅读参考]->(a)
            """, title=title, p_name=p_name)

        # 7. 症状池
        symptom_pool = [
            '备考噩梦', '自我怀疑', '未来虚无感', '精力耗竭', '社交退缩',
            '同辈压力焦虑', '整晚失眠', '食欲不振', '面试惊恐情景', '自我效能感低',
            '专业课畏难', '厌学情绪', '逃课行为', '笔记障碍', '易激惹',
            '寝室言语冲突', '疑病倾向', '过度警觉', '心碎感', '丧失生存意志',
            '强迫性查手机', '边缘感', '当众说话颤抖', '自闭行为', '过度敏感',
            '病态节食', '催吐行为', '体型扭曲感知', '强迫性洗手', '反复检查门窗'
        ]
        for s in symptom_pool:
            merge_node('症状', '名称', s)

        # 8. 治疗方案池
        treatment_pool = [
            '认知重组疗法', '接纳承诺疗法(ACT)', '叙事疗法', '正念减压法(MBSR)', '辩证行为疗法(DBT)',
            'SFBT焦点解决短期治疗', '萨提亚家庭治疗模型', '格式塔空椅子技术', '系统脱敏训练', '社交技巧训练',
            '森田疗法', '运动疗法', '绘画心理分析', '音乐疗法', '悲伤辅导',
            '人际动力学小组', '动机访谈法(MI)', '沙盘游戏治疗', '心理剧干预', '支持性心理治疗'
        ]
        for t in treatment_pool:
            merge_node('治疗方案', '名称', t, {'原理说明': '专业' + t + '理论基础'})

        # 9. 应对技巧池
        skill_pool = [
            '三栏法自动思维记录', 'STOP技术', '蝴蝶抱技术', '54321感官专注', '愤怒冰山分析',
            'DEAR MAN沟通技巧', '价值观拍卖会', '生命线回顾', '优点轰炸', '放松训练记录表',
            '时间管理四象限', '情绪调节饼图', '积极自我暗示', '三件好事打卡', '深呼吸2-4-8法',
            '渐进式肌肉放松', '社会支持系统图', '应对陈述句卡片', '行为实验表', '焦虑等级量表制作'
        ]
        for sk in skill_pool:
            merge_node('应对技巧', '名称', sk, {'操作步骤': '具体' + sk + '执行步骤'})

        # 10. 随机建立关系确保密度
        session.run("MATCH (p:心理问题), (s:症状) WITH p, s WHERE rand() < 0.3 MERGE (p)-[:具有症状 {匹配权重: rand()}]->(s)")
        session.run("MATCH (p:心理问题), (t:治疗方案) WITH p, t WHERE rand() < 0.3 MERGE (p)-[:治疗方案 {有效性: '推荐'}]->(t)")
        session.run("MATCH (t:治疗方案), (sk:应对技巧) WITH t, sk WHERE rand() < 0.3 MERGE (t)-[:包含技巧]->(sk)")

        # 11. 关键风险触发
        critical_links = [('丧失生存意志', '极高'), ('催吐行为', '高危')]
        for s, r in critical_links:
            session.run("MATCH (sym:症状 {名称: $s}), (risk:风险等级 {名称: $r}) MERGE (sym)-[:触发预警]->(risk)", s=s, r=r)

        # 12. 统计
        n = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        r = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
        missing_uuid = session.run("MATCH (n) WHERE n.uuid IS NULL RETURN count(n) AS c").single()["c"]
        print(f"Update Success! Nodes: {n}, Rels: {r}, Missing UUID: {missing_uuid}")

if __name__ == "__main__":
    rebuild_graph_with_uuids()
    driver.close()

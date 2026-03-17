import logging
from neo4j import GraphDatabase
from django.conf import settings

logger = logging.getLogger(__name__)

class Neo4jRepository:
    """
    封装预设好的安全 Cypher 模板与连接池
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jRepository, cls).__new__(cls)
            cls._instance.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return cls._instance

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def get_psychological_problem_graph(self, problem_name: str) -> dict:
        """
        根据名称查询心理问题全貌及其多跳关系，直接组装为 JSON 树
        此方法体现了在图谱端完成中英属性映射与嵌套推导的设计初衷。
        """
        query = '''
        MATCH (p:`心理问题` {`名称`: $problem_name})

        RETURN p {
            .uuid,
            name: p.`名称`,
            description: p.`描述`,
            severity: p.`严重程度`,

            symptoms: [ (p)-[r1:`具有症状`]->(s:`症状`) | s {
                name: s.`名称`,
                category: s.`类别`,
                weight: r1.`匹配权重`,
                
                risk_info: head([ (s)-[:`触发预警`]->(risk:`风险等级`)-[:`执行预案`]->(e:`应急预案`) | {
                    level: risk.`名称`,
                    action: e.`干预话术`,
                    contact: e.`资源`
                }])
            }],

            treatments: [ (p)-[r2:`治疗方案`]->(t:`治疗方案`) | t {
                name: t.`名称`,
                rationale: t.`原理说明`,
                effectiveness: r2.`有效性`,
                
                skills: [ (t)-[:`包含技巧`]->(c:`应对技巧`) | c {
                    name: c.`名称`,
                    steps: c.`操作步骤`
                }]
            }],

            campus_context: head([ (p)-[:`关联政策`]->(pol:`校园政策`)-[:`负责部门`]->(org:`校园机构`) | {
                policy_name: pol.`名称`,
                policy_detail: pol.`事项说明`,
                org_name: org.`名称`,
                location: org.`办公地点`,
                contact: org.`联系方式`
            }])
            
        } AS structured_json
        '''
        
        try:
            with self.driver.session() as session:
                result = session.run(query, problem_name=problem_name)
                record = result.single()
                if record:
                    return record["structured_json"]
                return None
        except Exception as e:
            logger.error(f"Neo4j query error: {str(e)}")
            # Fail-Fast: 立即校验并在底层记录，但不直接抛给前端，而是返回 None 走兜底
            return None

    def find_problem_by_symptoms(self, symptoms: list[str]) -> str | None:
        """
        根据一组症状名称，在图谱中反查最匹配的心理问题名称。
        采用统计匹配个数的方式进行简单的模糊定位。
        """
        if not symptoms:
            return None
            
        query = '''
        UNWIND $symptoms AS sym_name
        MATCH (s:`症状`) WHERE s.`名称` CONTAINS sym_name OR sym_name CONTAINS s.`名称`
        MATCH (p:`心理问题`)-[:`具有症状`]->(s)
        RETURN p.`名称` AS name, count(distinct s) AS score
        ORDER BY score DESC
        LIMIT 1
        '''
        
        try:
            with self.driver.session() as session:
                result = session.run(query, symptoms=symptoms)
                record = result.single()
                return record["name"] if record else None
        except Exception as e:
            logger.error(f"Neo4j symptom lookup error: {str(e)}")
            return None

neo4j_repo = Neo4jRepository()

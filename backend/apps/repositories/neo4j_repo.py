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
                .uuid,
                name: s.`名称`,
                weight: r1.`匹配权重`,
                
                risk_info: head([ (s)-[:`触发预警`]->(risk:`风险等级`)-[:`执行预案`]->(e:`应急预案`) | {
                    level: risk.`名称`,
                    action: e.`干预话术`,
                    contact: e.`资源`
                }])
            }][..10],

            treatments: [ (p)-[r2:`治疗方案`]->(t:`治疗方案`) | t {
                .uuid,
                name: t.`名称`,
                rationale: t.`原理`,
                effectiveness: r2.`有效性`,
                
                skills: [ (t)-[:`包含技巧`]->(c:`应对技巧`) | c {
                    .uuid,
                    name: c.`名称`,
                    steps: c.`步骤`
                }][..3]
            }][..5],

            campus_context: head([ (p)-[:`关联政策`]->(pol:`校园政策`)-[:`属于`]->(org:`校园机构`) | {
                policy_uuid: pol.uuid,
                policy_name: pol.`名称`,
                policy_detail: pol.`事项`,
                org_name: org.`名称`,
                location: org.`办公地点`,
                contact: org.`联系方式`
            }]),

            recommended_articles: [ (p)-[:`推荐文章`]->(art:`心理文章`) | art {
                .uuid,
                name: art.`名称`,
                author: art.`作者`,
                cover: art.`封面图`
            }],

            assessments: [ (p)-[:`具有症状`]->(s:`症状`)-[:`推荐测评`]->(scale:`测评量表`) | scale {
                .uuid,
                name: scale.`名称`,
                desc: scale.`描述`,
                total_questions: scale.`题目总数`
            }]
            
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
        采用评分机制进行模糊定位。
        """
        if not symptoms:
            return None
            
        query = '''
        UNWIND $symptoms AS sym_name
        MATCH (s:`症状`)
        WITH s, sym_name,
             CASE 
                WHEN s.`名称` = sym_name THEN 10
                WHEN s.`名称` CONTAINS sym_name OR sym_name CONTAINS s.`名称` THEN 5
                WHEN size(sym_name) >= 2 AND (s.`名称` CONTAINS substring(sym_name, 0, 2) OR sym_name CONTAINS substring(s.`名称`, 0, 2)) THEN 2
                ELSE 0 
             END AS match_score
        WHERE match_score > 0
        MATCH (p:`心理问题`)-[:`具有症状`]->(s)
        RETURN p.`名称` AS name, sum(match_score) AS score
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

    def find_policy_by_keyword(self, keyword: str) -> dict | None:
        """
        专门查询校园政策节点，支持模糊匹配名称或事项。
        """
        query = '''
        MATCH (pol:`校园政策`)
        WHERE pol.`名称` CONTAINS $keyword OR pol.`事项` CONTAINS $keyword
        MATCH (pol)-[:`属于`]->(org:`校园机构`)
        RETURN {
            policy_uuid: pol.uuid,
            policy_name: pol.`名称`,
            policy_detail: pol.`事项`,
            org_name: org.`名称`,
            location: org.`办公地点`,
            contact: org.`联系方式`
        } AS policy_node
        LIMIT 1
        '''
        try:
            with self.driver.session() as session:
                result = session.run(query, keyword=keyword)
                record = result.single()
                if record:
                    # 为了兼容 generate_response 的 Prompt 结构，将其包装在 campus_context 中
                    return {"campus_context": record["policy_node"]}
                return None
        except Exception as e:
            logger.error(f"Neo4j policy lookup error: {str(e)}")
            return None

neo4j_repo = Neo4jRepository()

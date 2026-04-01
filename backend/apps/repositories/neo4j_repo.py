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

    def get_psychological_problem_graph(self, problem_name: str = None, uuid: str = None) -> dict:
        """
        深度获取心理问题关联的所有资源（文章、对策、政策、症状）。
        采用 Map Projection 字典投影，直接返回符合前端要求的嵌套 JSON。
        """
        if uuid:
            match_clause = "MATCH (p:`心理问题` {uuid: $uuid})"
            params = {"uuid": uuid}
        elif problem_name:
            match_clause = "MATCH (p:`心理问题`) WHERE p.`名称` CONTAINS $problem_name"
            params = {"problem_name": problem_name}
        else:
            return None

        query = match_clause + """
        WITH p LIMIT 1
        
        OPTIONAL MATCH (p)-[:`具有症状`]->(s:`症状`)
        WITH p, collect(DISTINCT s.`名称`)[..3] AS symptoms
        
        OPTIONAL MATCH (p)-[:`关联政策`]->(pol:`校园政策`)
        WITH p, symptoms, collect(DISTINCT pol { 
            .uuid, 
            name: pol.`名称`, 
            content: pol.`内容`, 
            department: pol.`部门` 
        })[..1] AS policies
        
        OPTIONAL MATCH (p)-[:`推荐文章`]->(art:`心理文章`)
        WITH p, symptoms, policies, collect(DISTINCT art { 
            .uuid, 
            name: art.`名称`, 
            cover: art.`封面图`, 
            url: art.url,
            summary: art.`内容摘要`
        })[..1] AS articles
        
        OPTIONAL MATCH (p)-[:`推荐方案`]->(c:`应对技巧`)
        WITH p, symptoms, policies, articles, collect(DISTINCT c { 
            .uuid, 
            name: c.`名称`, 
            content: c.`说明`,
            method: c.`方法`
        })[..1] AS treatments
        
        RETURN p {
            .uuid,
            .名称,
            .risk_level,
            .描述,
            symptoms: symptoms,
            campus_policies: policies,
            articles: articles,
            treatments: treatments
        } AS context
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                record = result.single()
                if record:
                    return record["context"]
                return None
        except Exception as e:
            logger.error(f"Neo4j deep query error: {str(e)}")
            return None

    def vector_search_candidates(self, embedding: list, top_k: int = 5) -> list:
        """
        [STUB] 利用 Neo4j 5.x 的向量索引进行候选节点初筛。
        """
        query = """
        CALL db.index.vector.queryNodes('problem_vector_index', $top_k, $embedding)
        YIELD node, score
        RETURN node {
            .uuid,
            .名称,
            .描述,
            score: score
        } AS result
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, embedding=embedding, top_k=top_k)
                return [record["result"] for record in result]
        except Exception as e:
            logger.error(f"Neo4j vector search failed: {str(e)}")
            return []

    def find_problem_by_symptoms(self, symptoms: list[str]) -> str | None:
        """
        根据一组症状名称，在图谱中反查最匹配的心理问题名称。
        """
        if not symptoms:
            return None
            
        query = '''
        UNWIND $symptoms AS sym_name
        MATCH (s:`症状`)
        WHERE s.`名称` CONTAINS sym_name OR sym_name CONTAINS s.`名称`
        MATCH (p:`心理问题`)-[:`具有症状`]->(s)
        RETURN p.`名称` AS name, count(s) AS score
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

    def find_problem_by_keyword(self, keyword: str) -> str | None:
        """
        根据关键词对心理问题的名称或描述进行模糊搜索。
        """
        if not keyword: return None
        
        query = '''
        MATCH (p:`心理问题`)
        WHERE p.`名称` CONTAINS $keyword OR $keyword CONTAINS p.`名称`
        OR p.`描述` CONTAINS $keyword
        RETURN p.`名称` AS name
        LIMIT 1
        '''
        try:
            with self.driver.session() as session:
                result = session.run(query, keyword=keyword)
                record = result.single()
                return record["name"] if record else None
        except Exception as e:
            logger.error(f"Neo4j keyword lookup error: {str(e)}")
            return None

    def find_policy_by_keyword(self, keyword: str) -> dict | None:
        """
        专门查询校园政策节点，支持模糊匹配。
        """
        query = '''
        MATCH (pol:`校园政策`)
        WHERE pol.`名称` CONTAINS $keyword OR pol.`内容` CONTAINS $keyword
        RETURN pol {
            .uuid,
            name: pol.`名称`,
            content: pol.`内容`,
            department: pol.`部门`
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

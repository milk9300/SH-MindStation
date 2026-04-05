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
        [Standard Fetch] 深度获取心理问题关联的所有基础资源（不包含时空上下文）。
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
        
        OPTIONAL MATCH (p)-[:`临床症状`]->(s:`症状`)
        WITH p, collect(DISTINCT s.`名称`)[..5] AS symptoms
        
        OPTIONAL MATCH (p)-[:`依据政策`]->(pol:`校园政策`)
        WITH p, symptoms, collect(DISTINCT pol { 
            .uuid, 
            name: pol.`名称`, 
            content: pol.`内容`, 
            department: COALESCE(pol.`部门`, '未知') 
        })[..2] AS policies
        
        OPTIONAL MATCH (p)-[:`科普阅读`]->(art:`文章`)
        WITH p, symptoms, policies, collect(DISTINCT art { 
            .uuid, 
            name: art.`名称`, 
            cover: art.`封面图`, 
            url: COALESCE(art.url, ''),
            summary: art.`内容摘要`
        })[..4] AS articles
        
        OPTIONAL MATCH (p)-[:`推荐干预`]->(c:`应对技巧`)
        WITH p, symptoms, policies, articles, collect(DISTINCT c { 
            .uuid, 
            name: c.`名称`, 
            content: c.`说明`,
            method: COALESCE(c.`方法`, '')
        })[..5] AS treatments
        
        RETURN p {
            .uuid,
            .名称,
            risk_level: p.`风险等级`,
            .category,
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

    def get_context_aware_graph(self, uuid: str, current_month: str) -> dict:
        """
        [Spatio-Temporal Aware] 获取带有校园事件（时间）和落地地点（空间）的增强推荐上下文。
        """
        query = """
        MATCH (p:`心理问题` {uuid: $uuid})
        
        // 1. 匹配当前月份触发的校园事件 (时间感知)
        OPTIONAL MATCH (e:`校园事件`)-[:`诱导场景`]->(p)
        WHERE e.`发生月份` CONTAINS $current_month
        WITH p, collect(DISTINCT e {
            name: e.`名称`,
            month: e.`发生月份`,
            description: COALESCE(e.`描述`, '当前月份诱发因素')
        }) AS events
        
        // 2. 匹配应对方案及其所在的物理地点 (空间感知)
        OPTIONAL MATCH (p)-[:`推荐干预`]->(r:`应对技巧`)
        OPTIONAL MATCH (r)-[:`建议物理场所`]->(loc:`校园地点`)
        WITH p, events, collect(DISTINCT r {
            .uuid,
            name: r.`名称`,
            method: COALESCE(r.`方法`, ''),
            content: r.`说明`,
            location: loc.`名称`,
            open_hours: loc.`开放时间`,
            contact: loc.`负责人`
        })[..5] AS treatments
        
        // 3. 匹配科普文章
        OPTIONAL MATCH (p)-[:`科普阅读`]->(art:`文章`)
        WITH p, events, treatments, collect(DISTINCT art {
            .uuid,
            name: art.`名称`,
            cover: art.`封面图`,
            url: COALESCE(art.url, ''),
            summary: art.`内容摘要`
        })[..4] AS articles
        
        // 4. 补充基础症状和政策信息
        OPTIONAL MATCH (p)-[:`临床症状`]->(s:`症状`)
        WITH p, events, treatments, articles, collect(DISTINCT s {
            name: s.`名称`
        })[..8] AS symptoms
        
        OPTIONAL MATCH (p)-[:`依据政策`]->(pol:`校园政策`)
        WITH p, events, treatments, articles, symptoms, collect(DISTINCT pol {
            .uuid,
            name: pol.`名称`,
            content: pol.`内容`,
            department: COALESCE(pol.`部门`, '未知')
        })[..2] AS policies
        
        RETURN {
            problem_name: p.`名称`,
            description: p.`描述`,
            risk_level: p.`风险等级`,
            current_events: events,
            symptoms: symptoms,
            treatments: treatments,
            articles: articles,
            policies: policies
        } AS context_card
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, uuid=uuid, current_month=current_month)
                record = result.single()
                return record["context_card"] if record else None
        except Exception as e:
            logger.error(f"Neo4j Context-Aware query error: {str(e)}")
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
        MATCH (p:`心理问题`)-[:`临床症状`]->(s)
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

    def get_entity_detail(self, uuid: str) -> dict:
        """
        [Entity Detail] 获取通用实体（应对技巧、症状、政策等）的详细信息及其反向关联的心理问题。
        """
        query = """
        MATCH (n {uuid: $uuid})
        
        // 反查关联的心理问题 (入边)
        OPTIONAL MATCH (p:`心理问题`)-[r]->(n)
        WITH n, collect(DISTINCT p {
            .uuid,
            name: p.`名称`,
            category: COALESCE(p.category, '心理健康'),
            risk_level: COALESCE(p.`风险等级`, '一般')
        }) AS related_problems
        
        // 如果是应对技巧，尝试获取建议地点
        OPTIONAL MATCH (n)-[:`建议物理场所`]->(loc:`校园地点`)
        
        RETURN n {
            .*,
            label: labels(n)[0],
            name: COALESCE(n.`名称`, n.name, '未命名实体'),
            // 聚合所有可能的描述性字段
            content: COALESCE(n.`内容`, n.`说明`, n.`描述`, n.`内容摘要`, '暂无详细描述'),
            method: COALESCE(n.`方法`, ''),
            location: loc.`名称`,
            open_hours: loc.`开放时间`,
            related_problems: related_problems
        } AS detail
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, uuid=uuid)
                record = result.single()
                if record:
                    return record["detail"]
                
                # 最后的兜底：如果 UUID 没中，且 UUID 看起来像个名称，尝试按名称查
                if len(uuid) < 30: # 假设 UUID 通常是 36 位，短的可能是名称
                    query_name = "MATCH (n) WHERE n.`名称` = $uuid RETURN n {.*, label: labels(n)[0], name: n.`名称`} AS detail"
                    res_name = session.run(query_name, uuid=uuid).single()
                    return res_name["detail"] if res_name else None
                    
                return None
        except Exception as e:
            logger.error(f"Neo4j entity detail query error: {str(e)}")
            return None

neo4j_repo = Neo4jRepository()

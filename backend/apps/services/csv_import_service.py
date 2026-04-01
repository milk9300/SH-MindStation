import pandas as pd
import logging
from neo4j import GraphDatabase
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

class CSVGraphImportService:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def clean_except_articles(self):
        """
        除了心理文章标签外的所有实体及其关系，全部移除。
        """
        logger.info("Cleaning graph nodes except '心理文章'...")
        query = "MATCH (n) WHERE NOT n:心理文章 DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query)
        logger.info("Cleanup complete.")

    def import_nodes(self, csv_path: str, label: str):
        """
        从CSV导入节点，使用uuid作为唯一约束 (MERGE)。
        """
        if not Path(csv_path).exists():
            logger.error(f"CSV file not found: {csv_path}")
            return

        df = pd.read_csv(csv_path)
        logger.info(f"Importing {len(df)} nodes with label '{label}' from {csv_path}...")

        # 动态构建 Cypher 语句，处理所有列作为属性
        columns = [col for col in df.columns if col != 'uuid']
        set_clauses = [f"n.`{col}` = row.`{col}`" for col in columns]
        
        query = f"""
        UNWIND $rows AS row
        MERGE (n:`{label}` {{uuid: row.uuid}})
        SET {', '.join(set_clauses)}
        """

        # 分批导入以防事务过大
        batch_size = 1000
        with self.driver.session() as session:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size].to_dict('records')
                session.run(query, rows=batch)
        
        logger.info(f"Imported label '{label}' successfully.")

    def import_edges(self, csv_path: str):
        """
        导入关系，基于source_uuid和target_uuid进行MERGE。
        具有严格校验：如果源或目标UUID不存在，则跳过。
        """
        if not Path(csv_path).exists():
            logger.error(f"CSV file not found: {csv_path}")
            return

        df = pd.read_csv(csv_path)
        logger.info(f"Importing {len(df)} relationships from {csv_path}...")

        query = """
        UNWIND $rows AS row
        MATCH (source {uuid: row.source_uuid})
        MATCH (target {uuid: row.target_uuid})
        CALL apoc.merge.relationship(source, row.relation, {}, {weight: row.weight}, target) YIELD rel
        RETURN count(rel)
        """
        # 注意：apoc.merge.relationship 用于动态关系类型
        # 如果没有 APOC，可以使用更基础的拼接方式（但在批导中较慢）
        # 这里先检查是否有 APOC，如果没有则降级
        
        with self.driver.session() as session:
            # 简单降级实现（不依赖 APOC，但支持动态关系类型需要一点技巧）
            # 由于关系类型通常在CSV中是有限的，我们可以按类型分组导入
            for rel_type in df['relation'].unique():
                type_df = df[df['relation'] == rel_type]
                sub_query = f"""
                UNWIND $rows AS row
                MATCH (source {{uuid: row.source_uuid}})
                MATCH (target {{uuid: row.target_uuid}})
                MERGE (source)-[r:`{rel_type}`]->(target)
                SET r.weight = row.weight
                """
                batch_size = 500
                for i in range(0, len(type_df), batch_size):
                    batch = type_df.iloc[i:i+batch_size].to_dict('records')
                    session.run(sub_query, rows=batch)
        
        logger.info("Relationships imported successfully.")

csv_import_service = CSVGraphImportService()

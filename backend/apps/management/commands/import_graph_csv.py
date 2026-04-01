import os
import logging
from django.core.management.base import BaseCommand
from apps.services.csv_import_service import CSVGraphImportService
from pathlib import Path

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import knowledge graph from CSV files using UUID-based merge logic.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean all nodes except "心理文章" before import.',
        )
        parser.add_argument(
            '--path',
            type=str,
            default='data/graph/csv',
            help='Directory containing CSV files.',
        )

    def handle(self, *args, **options):
        csv_root = Path(options['path'])
        service = CSVGraphImportService()
        
        try:
            if options['clean']:
                service.clean_except_articles()
                self.stdout.write(self.style.SUCCESS('Successfully cleaned graph (except articles).'))

            # 1. 第一阶段：实体导入 (Order matters to satisfy dependencies if any)
            nodes_dir = csv_root / "nodes"
            
            # 定义映射关系：文件名 -> Neo4j Label
            node_files = {
                "risk_levels.csv": "风险等级",
                "emergency_plans.csv": "应急预案",
                "policies.csv": "校园政策",
                "coping_skills.csv": "应对技巧",
                "symptoms.csv": "症状",
                "problems.csv": "心理问题"
            }
            
            for filename, label in node_files.items():
                file_path = nodes_dir / filename
                if file_path.exists():
                    service.import_nodes(str(file_path), label)
                    self.stdout.write(self.style.SUCCESS(f'Imported nodes from {filename} as {label}.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Skipping {filename}, file not found.'))

            # 2. 第二阶段：关系导入
            edges_dir = csv_root / "edges"
            for edge_file in edges_dir.glob("*.csv"):
                service.import_edges(str(edge_file))
                self.stdout.write(self.style.SUCCESS(f'Imported relationships from {edge_file.name}.'))

            self.stdout.write(self.style.SUCCESS('Knowledge graph import completed successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {str(e)}'))
            logger.exception("Graph import failed")
        finally:
            service.close()

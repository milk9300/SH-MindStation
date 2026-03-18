from rest_framework.views import APIView
from rest_framework.response import Response
from apps.repositories.neo4j_repo import neo4j_repo
from apps.services.audit_service import audit_service
from apps.models import User

class GraphDumpView(APIView):
    """
    导出全量(或部分)图谱数据用于 AntV G6 可视化渲染
    """
    def get(self, request):
        try:
            # 简化版：直接通过 Repository 执行原生 Cypher 获取 G6 格式数据
            query = '''
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN collect(distinct n) as nodes, collect(distinct r) as relationships
            '''
            with neo4j_repo.driver.session() as session:
                result = session.run(query).single()
                
                g6_nodes = []
                g6_edges = []
                
                # 处理节点
                if result and result['nodes']:
                    for node in result['nodes']:
                        label = list(node.labels)[0] if node.labels else 'Unknown'
                        props = dict(node)
                        
                        # 智能提取一个最核心的描述字段，避免全部拼接导致回显冗余
                        # 优先级：原理 > 步骤 > 诊断标准 > 描述
                        primary_desc = props.get('原理') or props.get('步骤') or props.get('诊断标准') or props.get('描述') or ''
                        
                        g6_nodes.append({
                            "id": str(node.id),
                            "uuid": props.get('uuid', ''),
                            "name": props.get('名称', '未命名'),
                            "label": label,
                            "description": primary_desc
                        })
                        
                # 处理连线
                if result and result['relationships']:
                    for rel in result['relationships']:
                        if rel is None: continue
                        g6_edges.append({
                            "source": str(rel.start_node.id),
                            "target": str(rel.end_node.id),
                            "label": rel.type
                        })
                        
                return Response({
                    "nodes": g6_nodes,
                    "edges": g6_edges
                })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": "Failed to dump graph data"}, status=500)


class EntityCreateView(APIView):
    """
    新建 Neo4j 实体节点
    """
    def post(self, request):
        try:
            name = request.data.get('name')
            label = request.data.get('label')
            
            if not name or not label:
                return Response({'error': '实体名称和类别不能为空'}, status=400)
                
            import uuid
            new_uuid = str(uuid.uuid4())
            
            query = f'''
            CREATE (n:`{label}` {{uuid: $uuid, 名称: $name, 描述: ''}})
            RETURN id(n) as node_id
            '''
            
            with neo4j_repo.driver.session() as session:
                result = session.run(query, uuid=new_uuid, name=name).single()
                node_id = result['node_id']
                
            # 记录审计日志
            handler = get_handler(request)
            audit_service.log_action(
                handler, 'KG_EDITOR', 'CREATE',
                f"创建了新节点[{label}]: 名称={name}",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '实体创建成功', 'node_id': node_id})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

def get_handler(request):
    auth_token = request.META.get('HTTP_AUTHORIZATION')
    return User.objects.filter(id=auth_token).first() if auth_token else None



class EntityDetailView(APIView):
    """
    获取、更新或删除指定的 Neo4j 实体节点及其关系
    """
    def get(self, request, node_id):
        """
        拉取节点详情及其所有外联关系数据
        """
        try:
            # 1. 获取节点属性
            node_query = "MATCH (n) WHERE id(n) = $node_id RETURN n"
            # 2. 获取节点关系 (按类型分组)
            rel_query = """
            MATCH (n)-[r]->(m) 
            WHERE id(n) = $node_id 
            RETURN type(r) as type, m.`名称` as target_name, m.uuid as target_uuid, id(m) as target_id, properties(r) as properties
            """
            
            with neo4j_repo.driver.session() as session:
                node_res = session.run(node_query, node_id=int(node_id)).single()
                if not node_res:
                    return Response({'error': '节点不存在'}, status=404)
                
                node = node_res['n']
                props = dict(node)
                label = list(node.labels)[0] if node.labels else 'Unknown'
                
                rel_res = session.run(rel_query, node_id=int(node_id))
                relationships = []
                for record in rel_res:
                    relationships.append({
                        "type": record['type'],
                        "target_id": str(record['target_id']),
                        "target_uuid": record['target_uuid'],
                        "target_name": record['target_name'],
                        "properties": record['properties']
                    })
                
                return Response({
                    "id": str(node.id),
                    "uuid": props.get('uuid', ''),
                    "name": props.get('名称', '未命名'),
                    "label": label,
                    "properties": props,
                    "relationships": relationships
                })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def put(self, request, node_id):
        try:
            data = request.data
            name = data.get('name')
            description = data.get('description', '')

            if not name:
                return Response({'error': '实体名称不能为空'}, status=400)

            # 1. 先查出节点现有的属性键，避免盲目 SET 导致多个描述字段并存
            check_query = "MATCH (n) WHERE id(n) = $node_id RETURN keys(n) as keys"
            target_keys = {'原理', '步骤', '诊断标准', '描述'}
            found_keys = []
            
            with neo4j_repo.driver.session() as session:
                res = session.run(check_query, node_id=int(node_id)).single()
                if res:
                    found_keys = [k for k in res['keys'] if k in target_keys]
            
            # 2. 构造动态 SET 子句
            # 如果没找到任何已知描述字段，则默认更新/创建 '描述' 字段
            if not found_keys:
                found_keys = ['描述']
            
            set_clauses = [f"n.`{k}` = $desc" for k in found_keys]
            query = f'''
            MATCH (n) WHERE id(n) = $node_id
            SET n.名称 = $name, {", ".join(set_clauses)}
            RETURN n
            '''
            
            with neo4j_repo.driver.session() as session:
                result = session.run(query, node_id=int(node_id), name=name, desc=description).single()
                if not result:
                    return Response({'error': '节点不存在'}, status=404)
                
            # 记录审计日志
            handler = get_handler(request)
            audit_service.log_action(
                handler, 'KG_EDITOR', 'UPDATE',
                f"更新了节点 ID={node_id}: 名称={name}",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '实体更新成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def delete(self, request, node_id):
        try:
            # 获取节点信息以便记录详述及校验删除权限
            node_name = "Unknown"
            node_labels = []
            info_query = "MATCH (n) WHERE id(n) = $node_id RETURN n.名称 as name, labels(n) as labels"
            with neo4j_repo.driver.session() as session:
                res = session.run(info_query, node_id=int(node_id)).single()
                if res:
                    node_name = res['name']
                    node_labels = res['labels']
                    
            if '心理文章' in node_labels or '测评量表' in node_labels:
                from rest_framework.response import Response
                return Response({'error': '此节点受系统严格管控，不可在图谱直接删除。请前往左侧菜单的对应的【科普文章管理】或【心理量表管理】界面中将其删除，图谱节点将随之自动移除。'}, status=400)

            # 删除节点及其所有连带关联关系
            query = '''
            MATCH (n) WHERE id(n) = $node_id
            DETACH DELETE n
            '''
            with neo4j_repo.driver.session() as session:
                session.run(query, node_id=int(node_id))
            
            # 记录审计日志
            handler = get_handler(request)
            audit_service.log_action(
                handler, 'KG_EDITOR', 'DELETE',
                f"删除了节点 ID={node_id}, 名称={node_name}",
                request.META.get('REMOTE_ADDR')
            )
                
            return Response({'message': '实体删除成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class EdgeManagementView(APIView):
    """
    图谱关系（连线）管理：建立、更新属性、解绑
    """
    def post(self, request):
        """
        建立或更新关系
        """
        source_id = request.data.get('source_id')
        target_uuid = request.data.get('target_uuid')
        rel_type = request.data.get('rel_type')
        properties = request.data.get('properties', {})

        if not all([source_id, target_uuid, rel_type]):
            return Response({'error': '缺失关键参数'}, status=400)

        query = f'''
        MATCH (a) WHERE id(a) = $source_id
        MATCH (b {{uuid: $target_uuid}})
        MERGE (a)-[r:`{rel_type}`]->(b)
        SET r += $properties
        RETURN r
        '''
        try:
            with neo4j_repo.driver.session() as session:
                session.run(query, source_id=int(source_id), target_uuid=target_uuid, properties=properties)
            
            # 记录审计日志
            handler = get_handler(request)
            audit_service.log_action(
                handler, 'KG_EDITOR', 'LINK',
                f"建立了关系: Node({source_id}) -[{rel_type}]-> Node({target_uuid})",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '关系更新成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def delete(self, request):
        """
        解除关系
        """
        source_id = request.query_params.get('source_id')
        target_uuid = request.query_params.get('target_uuid')
        rel_type = request.query_params.get('rel_type')

        if not all([source_id, target_uuid, rel_type]):
            return Response({'error': '缺失参数'}, status=400)

        query = f'''
        MATCH (a)-[r:`{rel_type}`]->(b {{uuid: $target_uuid}})
        WHERE id(a) = $source_id
        DELETE r
        '''
        try:
            with neo4j_repo.driver.session() as session:
                session.run(query, source_id=int(source_id), target_uuid=target_uuid)
            
            # 记录审计日志
            handler = get_handler(request)
            audit_service.log_action(
                handler, 'KG_EDITOR', 'UNLINK',
                f"解除了关系: Node({source_id}) -[{rel_type}]-> Node({target_uuid})",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '关系解除成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class EntitySearchView(APIView):
    """
    提供实体节点的远程模糊搜索，用于建立关联
    """
    def get(self, request):
        keyword = request.query_params.get('q', '')
        if not keyword:
            return Response([])

        query = '''
        MATCH (n)
        WHERE n.`名称` CONTAINS $keyword
        RETURN n.uuid as uuid, n.`名称` as name, labels(n)[0] as label
        LIMIT 20
        '''
        try:
            with neo4j_repo.driver.session() as session:
                result = session.run(query, keyword=keyword)
                nodes = [{
                    "uuid": record['uuid'],
                    "name": record['name'],
                    "label": record['label']
                } for record in result]
                return Response(nodes)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def _get_handler(self, request):
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        return User.objects.filter(id=auth_token).first() if auth_token else None

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from apps.repositories.neo4j_repo import neo4j_repo
from apps.services.audit_service import audit_service
from apps.models import User

class GraphDumpView(APIView):
    """
    导出图谱数据用于 AntV G6 可视化渲染。支持全量和初始(核心)加载。
    """
    def get(self, request):
        mode = request.query_params.get('mode', 'full') # initial | full
        try:
            if mode == 'initial':
                # 初始模式：返回空，由用户通过搜索开始探索
                return Response({
                    "nodes": [],
                    "edges": []
                })
            else:
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
            return Response({"error": f"Failed to dump graph data: {str(e)}"}, status=500)

class EntityNeighborsView(APIView):
    """
    拉取指定节点的邻居节点及关系，用于按需动态拓展
    """
    def get(self, request, node_id):
        try:
            # 这里的 node_id 是 Neo4j 的原生 ID
            query = '''
            MATCH (n) WHERE id(n) = $node_id
            OPTIONAL MATCH (n)-[r]-(m)
            RETURN n, collect(distinct m) as neighbors, collect(distinct r) as relationships
            '''
            with neo4j_repo.driver.session() as session:
                result = session.run(query, node_id=int(node_id)).single()
                if not result:
                    return Response({"error": "Node not found"}, status=404)
                
                g6_nodes = []
                g6_edges = []
                
                def _build_g6_node(node):
                    label = list(node.labels)[0] if node.labels else 'Unknown'
                    props = dict(node)
                    primary_desc = props.get('原理') or props.get('步骤') or props.get('诊断标准') or props.get('描述') or ''
                    return {
                        "id": str(node.id),
                        "uuid": props.get('uuid', ''),
                        "name": props.get('名称', '未命名'),
                        "label": label,
                        "description": primary_desc
                    }

                # 邻居节点 (过滤掉可能的 None)
                for neighbor in result['neighbors']:
                    if neighbor:
                        g6_nodes.append(_build_g6_node(neighbor))
                
                # 处理连线
                for rel in result['relationships']:
                    if rel:
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
            return Response({"error": str(e)}, status=500)


class EntityCreateView(APIView):
    """
    新建 Neo4j 实体节点
    """
    permission_classes = [permissions.IsAuthenticated]
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
            handler = self.request.user if self.request.user.is_authenticated else None
            audit_service.log_action(
                handler, 'KG_EDITOR', 'CREATE',
                f"创建了新节点[{label}]: 名称={name}",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '实体创建成功', 'node_id': node_id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class EntityDetailView(APIView):
    """
    获取、更新或删除指定的 Neo4j 实体节点及其关系
    """
    permission_classes = [permissions.IsAuthenticated]
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
            description = data.get('description')
            properties = data.get('properties', {})

            if not name and not properties:
                return Response({'error': '未提供任何更新内容'}, status=400)

            # 1. 基础属性映射 (兼容旧前端或顶层参数)
            update_props = {}
            if name:
                update_props['名称'] = name
            
            # 处理动态属性字典
            if properties:
                update_props.update(properties)
            
            # 处理顶层 description 兼容性 (回退到 Neo4j 已有的描述类字段)
            if description is not None:
                check_query = "MATCH (n) WHERE id(n) = $node_id RETURN keys(n) as keys"
                target_keys = {'原理', '步骤', '诊断标准', '描述'}
                found_keys = []
                
                with neo4j_repo.driver.session() as session:
                    res = session.run(check_query, node_id=int(node_id)).single()
                    if res:
                        found_keys = [k for k in res['keys'] if k in target_keys]
                
                if not found_keys:
                    found_keys = ['描述']
                
                for k in found_keys:
                    update_props[k] = description

            # 2. 执行动态增量更新
            query = f'''
            MATCH (n) WHERE id(n) = $node_id
            SET n += $props
            RETURN n
            '''
            
            with neo4j_repo.driver.session() as session:
                result = session.run(query, node_id=int(node_id), props=update_props).single()
                if not result:
                    return Response({'error': '节点不存在'}, status=status.HTTP_404_NOT_FOUND)
                
            # 记录审计日志
            handler = self.request.user if self.request.user.is_authenticated else None
            audit_service.log_action(
                handler, 'KG_EDITOR', 'UPDATE',
                f"更新了节点 ID={node_id}: {update_props}",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '实体更新成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            handler = self.request.user if self.request.user.is_authenticated else None
            audit_service.log_action(
                handler, 'KG_EDITOR', 'DELETE',
                f"删除了节点 ID={node_id}, 名称={node_name}",
                request.META.get('REMOTE_ADDR')
            )
                
            return Response({'message': '实体删除成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EdgeManagementView(APIView):
    """
    图谱关系（连线）管理：建立、更新属性、解绑
    """
    permission_classes = [permissions.IsAuthenticated]
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
            # 安全转换 source_id
            try:
                sid = int(source_id)
            except (ValueError, TypeError):
                return Response({'error': '无效的源节点 ID'}, status=status.HTTP_400_BAD_REQUEST)

            with neo4j_repo.driver.session() as session:
                session.run(query, source_id=sid, target_uuid=target_uuid, properties=properties)
            
            # 记录审计日志
            handler = self.request.user if self.request.user.is_authenticated else None
            audit_service.log_action(
                handler, 'KG_EDITOR', 'LINK',
                f"建立了关系: Node({source_id}) -[{rel_type}]-> Node({target_uuid})",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '关系更新成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            # 安全转换 source_id
            try:
                sid = int(source_id)
            except (ValueError, TypeError):
                return Response({'error': '无效的源节点 ID'}, status=status.HTTP_400_BAD_REQUEST)

            with neo4j_repo.driver.session() as session:
                session.run(query, source_id=sid, target_uuid=target_uuid)
            
            # 记录审计日志
            handler = self.request.user if self.request.user.is_authenticated else None
            audit_service.log_action(
                handler, 'KG_EDITOR', 'UNLINK',
                f"解除了关系: Node({source_id}) -[{rel_type}]-> Node({target_uuid})",
                request.META.get('REMOTE_ADDR')
            )
            return Response({'message': '关系解除成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from apps.services.graph_service import graph_service

class KnowledgeDetailView(APIView):
    """
    提供心理问题的全量知识图谱上下文（用于知识库详情页）
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, uuid):
        try:
            # 1. 获取深度背景
            context = graph_service.fetch_deep_context(uuid)
            if not context:
                return Response({'error': '未找到相关知识'}, status=status.HTTP_404_NOT_FOUND)
            
            # 2. 补全静态资源 URL
            # 注意：chat_service 中也有类似的 _fix_card_urls 逻辑，
            # 为了保持 API 的自闭环，我们在 View 层也做一次简单的 URL 修复。
            from django.conf import settings
            backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
            
            def _fix_urls(obj):
                if isinstance(obj, list):
                    for i in obj: _fix_urls(i)
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        if k in ['cover', 'image', 'avatar'] and isinstance(v, str) and v and not v.startswith('http'):
                            obj[k] = f"{backend_url}/{v.lstrip('/')}"
                        _fix_urls(v)
            
            _fix_urls(context)
            return Response(context)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        RETURN id(n) as node_id, n.uuid as uuid, n.`名称` as name, labels(n)[0] as label
        LIMIT 20
        '''
        try:
            with neo4j_repo.driver.session() as session:
                result = session.run(query, keyword=keyword)
                nodes = [{
                    "id": str(record['node_id']),
                    "uuid": record['uuid'],
                    "name": record['name'],
                    "label": record['label']
                } for record in result]
                return Response(nodes)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KnowledgeHomeView(APIView):
    """
    提供知识库首页数据：热门标签、分类筛选、搜索列表
    """
    def get(self, request):
        query_str = request.query_params.get('q', '')
        label_filter = request.query_params.get('label', '全部')
        
        # 1. 热门搜索/推荐 (选取连接数较多的节点作为探索入口)
        hot_query = """
        MATCH (n)
        WHERE labels(n)[0] IN ['心理问题', '应对技巧', '校园政策', '症状']
        RETURN n.`名称` as name, count{(n)--()} as connection_count
        ORDER BY connection_count DESC
        LIMIT 8
        """
        
        # 2. 列表查询分页参数
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 30))
        except (ValueError, TypeError):
            page, page_size = 1, 30
            
        skip = (page - 1) * page_size
        list_params = {"keyword": query_str, "skip": skip, "limit": page_size}
        
        cypher_filter = ""
        # 安全校验标签，防止注入
        valid_labels = ['心理问题', '应对技巧', '校园政策', '症状']
        if label_filter != '全部' and label_filter in valid_labels:
            cypher_filter = f":`{label_filter}`"
            
        list_query = f"""
        MATCH (n{cypher_filter})
        WHERE (n.`名称` CONTAINS $keyword OR n.`描述` CONTAINS $keyword OR n.`内容` CONTAINS $keyword OR n.`内容摘要` CONTAINS $keyword)
        AND labels(n)[0] IN ['心理问题', '应对技巧', '校园政策', '症状']
        RETURN n.uuid as uuid, n.`名称` as name, labels(n)[0] as label, 
               COALESCE(n.`描述`, n.`内容`, n.`内容摘要`, n.`说明`, '') as content,
               COALESCE(n.`封面图`, n.`cover`, '') as cover
        SKIP $skip LIMIT $limit
        """
        
        try:
            with neo4j_repo.driver.session() as session:
                # 获取热门标签
                hot_res = session.run(hot_query)
                hot_tags = [r['name'] for r in hot_res]
                
                # 获取列表结果
                list_res = session.run(list_query, **list_params)
                entities = []
                
                # 获取后端基础 URL 用于拼接图片路径
                from django.conf import settings
                backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
                
                for r in list_res:
                    cover = r['cover']
                    if cover and not cover.startswith('http'):
                        cover = f"{backend_url}/{cover.lstrip('/')}"
                        
                    entities.append({
                        "uuid": r['uuid'],
                        "name": r['name'],
                        "label": r['label'],
                        "content": r['content'][:80] + ('...' if len(r['content']) > 80 else ''),
                        "cover": cover
                    })
                
                # 固定的业务分类
                categories = [
                    {"id": "全部", "name": "全部"},
                    {"id": "心理问题", "name": "心理问题"},
                    {"id": "应对技巧", "name": "应对技巧"},
                    {"id": "校园政策", "name": "校园政策"},
                    {"id": "症状", "name": "症状"}
                ]
                
                return Response({
                    "categories": categories,
                    "hot_tags": hot_tags,
                    "entities": entities,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "has_more": len(entities) == page_size
                    }
                })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

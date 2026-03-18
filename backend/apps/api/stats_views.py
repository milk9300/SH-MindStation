from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.db.models.functions import TruncDate
from apps.models import User, ChatSession, CrisisAlertLog
from apps.repositories.neo4j_repo import neo4j_repo
from datetime import timedelta
from django.utils import timezone

class DashboardStatsView(APIView):
    """
    提供给数据大盘的全局聚合统计 API
    """
    def get(self, request):
        try:
            today = timezone.now().date()
            seven_days_ago = today - timedelta(days=7)

            # 1. 活跃会话数 (总计与今日)
            total_sessions = ChatSession.objects.count()
            today_sessions = ChatSession.objects.filter(created_at__date=today).count()

            # 2. 高危预警 (总计与待处理)
            total_alerts = CrisisAlertLog.objects.count()
            pending_alerts = CrisisAlertLog.objects.filter(status='pending').count()

            # 3. 获取最近 7 天的预警趋势折线图数据
            alert_trends = (
                CrisisAlertLog.objects.filter(created_at__date__gte=seven_days_ago)
                .annotate(date=TruncDate('created_at'))
                .values('date')
                .annotate(count=Count('id'))
                .order_by('date')
            )
            # 补齐 7 天数据（防止某天是 0 没查出来）
            trend_dict = {str(item['date']): item['count'] for item in alert_trends}
            dates_list = [(seven_days_ago + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
            trend_data = [trend_dict.get(d, 0) for d in dates_list]

            # 4. 获取触发最频繁的 Top 10 症状条形图数据
            top_symptoms = (
                CrisisAlertLog.objects.values('trigger_symptom')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )

            # 5. Neo4j 图谱总节点规模 (需要连图数据库)
            neo4j_nodes_count = 0
            try:
                with neo4j_repo.driver.session() as session:
                    res = session.run("MATCH (n) RETURN count(n) as node_count").single()
                    if res:
                        neo4j_nodes_count = res["node_count"]
            except Exception as e:
                print(f"Neo4j query failed: {e}")

            return Response({
                "summary": {
                    "total_sessions": total_sessions,
                    "today_sessions": today_sessions,
                    "total_alerts": total_alerts,
                    "pending_alerts": pending_alerts,
                    "total_nodes": neo4j_nodes_count
                },
                "trends": {
                    "dates": dates_list,
                    "counts": trend_data
                },
                "top_symptoms": [
                    {"name": item['trigger_symptom'], "value": item['count']} for item in top_symptoms
                ]
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": "Failed to aggregate stats", "detail": str(e)}, status=500)

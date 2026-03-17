from rest_framework.views import APIView
from rest_framework.response import Response

# 绝对不写任何业务逻辑，只负责接收请求、参数校验、返回格式

class HealthCheckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})

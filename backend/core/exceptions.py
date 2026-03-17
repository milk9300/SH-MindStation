from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    """
    全局统一异常处理
    """
    response = exception_handler(exc, context)
    return response

from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import set_rollback


def exception_handler(exc, context):
    """
    自定义异常
    :exc 本次发生的异常对象
    :context 本次发生异常时的上下文环境信息， 字典
    """

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait
        if isinstance(exc.detail, (list, dict)):
            if isinstance(exc.detail, list):
                errors = exc.detail
            else:
                # print(exc.detail.items())
                # print("**************************************")
                # print(f"exc:{exc.detail}")
                try:
                    errors = "".join([k + v[0] for k, v in exc.detail.items()])
                except Exception as e:
                    errors_data = {k: v[0] for k, v in exc.detail.items()}
                    errors = errors_data['messages'][0]['message']
        else:
            errors = exc.detail

        set_rollback()
        return Response({'code': 100, 'msg': errors, 'data': []}, status=exc.status_code, headers=headers)


class ParamsException(APIException):
    """
    serializers自定义错误响应
    """

    def __init__(self, error, code):
        self.detail = error
        self.status_code = code

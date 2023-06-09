from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['code'] = response.status_code

    return response


class ParamsException(APIException):
    """
    serializers自定义错误响应
    """

    def __init__(self, error, code):
        self.detail = error
        self.status_code = code

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backends.settings import MY_HOST
from backends.utils import fun_test
from interface.exception import ParamsException
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


@api_view(["GET"])
def fun_list(request):
    # fun_list = [x for x in dir(fun_test) if x.startswith('__') and not x.endswith("__")]
    fun_list = [{"value": x, "label": getattr(fun_test, x).__annotations__.get('return')} for x in dir(fun_test) if
                x.startswith('__') and not x.endswith("__")]
    return Response({'code': 200, 'detail': '成功', 'data': fun_list},
                    status=status.HTTP_200_OK)


# @swagger_auto_schema(
#     manual_parameters=[
#         openapi.Parameter('func', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,
#                           required=True)]
# )
@swagger_auto_schema(
    method='GET',
    manual_parameters=[
        openapi.Parameter('func', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,
                          required=True)]
)
@api_view(["GET"])
def fun_info(request):
    func = request.query_params.get('func')
    fun_info = getattr(fun_test, func).__annotations__.copy()
    print(fun_info)
    fun_info.popitem()
    info_list = [{"name": key, "type": fun_info[key], "value": ""} for key in fun_info]
    return Response({'code': 200, 'detail': '成功', 'data': info_list},
                    status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='POST',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['option', 'params'],
        properties={
            'option': openapi.Schema(type=openapi.TYPE_STRING),
            'params': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING))
        },
    )
)
@api_view(["POST"])
def fun_result(request):
    """
    pa
    """
    print(request.data)
    option = request.data.get('option', None)
    print(option)
    params = request.data.get('params', None)
    print(params)
    if not option:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        exp = "${" + f"{option}({','.join(params)})," + "}"
        print(exp)
        result = getattr(fun_test, option)(*params)
    except Exception as e:
        raise ParamsException(e.__str__(), 403)
    return Response({'code': 200, 'detail': '成功', 'data': {'result': result, 'exp': exp}},
                    status=status.HTTP_200_OK)


@api_view(["GET"])
def xmind2case(request):
    url = f"http://{MY_HOST}:{5501}/"
    return Response({'code': 200, 'detail': '成功', 'data': {'url': url}},
                    status=status.HTTP_200_OK)

import ast
import threading

import requests
import urllib3
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
#
# from backends.settings import BASE_DIR, MEDIA_ROOT
# from backends.utils import fun_test
from backends.utils import permissions
from backends.utils.common import *
from .apscheduler_job import ApschedulerJob
from .serializer import *

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Create your views here.


# 自定义用户认证校验
class CustomAuth(ModelBackend):
    """自定义用户认证模块"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(Q(username=username) | Q(mobile=username))
            print(user)
            if user.check_password(password):
                return user
        except Exception as e:
            print(e)
            return None


# 自定义分页参数
class MyPageNum(PageNumberPagination):
    page_size_query_param = "pageSize"
    page_query_param = "page"


# 自定义model返回格式模板
class MyModelViewSet(ModelViewSet):
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({'code': 200, 'detail': '更新成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({'code': 200, 'detail': '创建成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({'code': 200, 'detail': '获取成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({'code': 200, 'detail': '获取成功', 'data': response.data},
                        headers=response.headers,
                        status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({'code': 200, 'detail': '删除成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)


# 注册
class UserSignupAPIView(CreateAPIView):
    serializer_class = UserSignupSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = serializer.instance
        refresh, token = get_tokens_for_user(user)
        # token, _ = Token.objects.get_or_create(user=user)
        data = {"code": 200, "detail": "成功",
                "data": {
                    "refresh": refresh,
                    "token": token,
                    "username": user.username,
                    "user_id": user.pk,
                    "login_time": get_now_time()
                }}

        return Response(
            data=data,
            status=status.HTTP_201_CREATED
        )


# 登录
class UserSigninAPIView(GenericAPIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = UserSigninSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        refresh, token = get_tokens_for_user(user)
        # token, _ = Token.objects.get_or_create(user=user)
        data = {"code": 200, "detail": "成功",
                "data": {
                    "refresh": refresh,
                    "token": token,
                    "username": user.username,
                    "user_id": user.pk,
                    "login_time": get_now_time()
                }
                }
        return Response(
            data=data,
            status=status.HTTP_200_OK
        )


# 修改密码
class ChangePasswordAPIView(GenericAPIView):
    permission_classes = [permissions.IsOwnerOrReadOnly]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        refresh, token = get_tokens_for_user(user)
        # token, _ = Token.objects.get_or_create(user=user)
        data = {"code": 200, "msg": "成功",
                "data": {
                    "refresh": refresh,
                    "token": token,
                    "username": user.username,
                    "user_id": user.pk,
                    "login_time": get_now_time()
                }
                }
        return Response(
            data=data,
            status=status.HTTP_200_OK
        )


# 项目
class ProjectModelViewSet(MyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectModelSerializer
    # 需要过滤的查询条件数据
    filterset_fields = ('id', 'title', 'creator__username')
    pagination_class = MyPageNum
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(methods=['delete'], detail=False)
    def batch_delete(self, request, *args, **kwargs):
        ids = request.query_params.get('ids', None)
        if not ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pks = ids.split(',')
        Project.objects.filter(pk__in=pks).filter(creator_id=self.request.user).delete()
        return Response({'code': 200, 'detail': '成功', 'data': []},
                        status=status.HTTP_200_OK)


# 接口
class ApiModelViewSet(MyModelViewSet):
    # queryset = Api.objects.filter(~Q(project=None)).select_related('project')
    queryset = Api.objects.all().select_related('project', 'creator')
    serializer_class = ApiModelSerializer
    action_serializers = {
        'retrieve': ApiModelDetailSerializer,
        'partial_update': ApiModelDetailSerializer,
        'update': ApiModelDetailSerializer,
        'create': ApiModelDetailSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]

        return super(ApiModelViewSet, self).get_serializer_class()

    # 需要过滤的查询条件数据
    filterset_fields = ('id', 'title', 'project__id', 'creator__username')
    pagination_class = MyPageNum
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(methods=['get'], detail=False)
    def get_temp_api(self, request, *args, **kwargs):
        filters = {
            "project": None,
            "creator": self.request.user
        }
        queryset = Api.objects.filter(**filters).values('id', 'title', 'method', 'url')
        page = self.paginate_queryset(queryset)
        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['post'], detail=False)
    def api_copy(self, request):
        api_id = request.data.get('id', None)
        if not api_id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        api_obj = Api.objects.get(id=api_id)
        api_obj.pk = None
        api_obj.id = None
        api_obj.creator = self.request.user
        api_obj.title = f"{api_obj.title}_copy"
        api_obj.save()
        api_data = {
            "id": api_obj.id,
            "title": api_obj.title,
            "method": api_obj.method,
            "url": api_obj.url
        }
        return Response({'code': 200, 'detail': '成功', 'data': api_data},
                        status=status.HTTP_200_OK)

    @action(methods=['delete'], detail=False)
    def batch_delete(self, request, *args, **kwargs):
        ids = request.query_params.get('ids', None)
        if not ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pks = ids.split(',')
        Api.objects.filter(pk__in=pks).filter(creator_id=self.request.user).delete()
        return Response({'code': 200, 'detail': '成功', 'data': []},
                        status=status.HTTP_200_OK)

    #  单接口调试执行
    @action(methods=['post'], detail=False)
    def api_send(self, request):
        print_switch(False)
        data = request.data
        if not data:
            return Response(status=status.HTTP_404_NOT_FOUND)
        project = data.get('project')
        config = None
        config_id = data.get("api_env")
        if project:
            filters = {
                "project": project,
                "type": 0
            }
            g_config = get_dict(Config.objects.filter(**filters).first().variables)
            config = get_config(config_id)
            g_config.update(config['variables'])
            config['variables'] = g_config
        params = get_request_data(data, config)
        postConditionResult = []
        postCondition = params.pop('postCondition')
        s = requests.Session()
        res = None
        req = None
        start_time = int(round(time.time() * 1000))
        try:
            res = s.request(**params, verify=False, timeout=5)
            res.encoding = "utf-8"
            # res.raise_for_status()
            my_post_condition(res, postCondition, postConditionResult, config_id=config_id)
            # print(postConditionResult)
            req = get_request_info(res.request)
            return Response(
                {'code': 200, 'detail': '成功', "data": res.text, "postConditionResult": postConditionResult,
                 "request": req,
                 "duration": int(res.elapsed.total_seconds() * 1000), "startTime": start_time,
                 "status": res.status_code}, status=status.HTTP_200_OK)
        except Exception as e:
            if res:
                duration = int(res.elapsed.total_seconds() * 1000)
                _status = res.status_code
            else:
                duration = int(round(time.time() * 1000)) - start_time
                _status = status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response(
                {'code': 100, 'detail': '失败', "data": e.__str__(), "postConditionResult": postConditionResult,
                 "request": req,
                 "duration": duration, "startTime": start_time, "status": _status},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            s.close()

    #  批量调试执行
    @action(methods=['post'], detail=False)
    def apis_send(self, request):
        print_switch(False)
        pre_text = None
        data = request.data
        if not data.get("ids"):
            return Response(status=status.HTTP_404_NOT_FOUND)
        obj_list = Api.objects.filter(pk__in=data["ids"]).values('id', 'method', 'url', 'bodyType', 'queryData',
                                                                 'headersData', 'cookies', 'formData',
                                                                 'formUrlencodedData',
                                                                 'rawData', 'postCondition', 'api_env').order_by('id')
        if obj_list.count() > 1 and data['async'] == 1:
            print("开始异步接口测试")
            asyncio.run(main(obj_list))
        else:
            print("开始同步接口测试")
            with requests.Session() as s:
                for i in obj_list:
                    config = None
                    if i.get("api_env"):
                        config = get_config(i.get('api_env'))
                    params = get_request_data(i, config)
                    postConditionResult = []
                    postCondition = params.pop('postCondition')
                    start_time = int(time.time() * 1000)
                    res = None
                    response = None
                    try:
                        res = s.request(**params, verify=False, timeout=5)
                        my_post_condition(res, postCondition, postConditionResult, option=1)
                        try:
                            res_content = res.json()
                        except:
                            res_content = res.text
                        response = {
                            "data": res_content,
                            "postConditionResult": postConditionResult,
                            "status": res.status_code,
                            "startTime": start_time,
                            "duration": int(res.elapsed.total_seconds() * 1000)
                        }
                    except Exception as e:
                        if res:
                            duration = int(res.elapsed.total_seconds() * 1000)
                            _status = res.status_code
                        else:
                            duration = int(time.time() * 1000) - start_time
                            _status = status.HTTP_500_INTERNAL_SERVER_ERROR
                        response = {
                            "data": e.__str__(),
                            "postConditionResult": postConditionResult,
                            "status": _status,
                            "startTime": start_time,
                            "duration": duration
                        }
                    finally:
                        api = Api.objects.filter(id=i['id'])
                        api.update(status=response['status'])
                        if len(obj_list) == 1:
                            # pre_data = params.get('data')
                            pre_data = files_text = ""
                            if params.get('data'):
                                pre_data = json_str(params.get('data'))
                            if params.get('json'):
                                pre_data = json_str(params.get('json'))
                            pre_result = response.get('data')
                            if isinstance(pre_result, dict):
                                pre_result = json_str(pre_result)
                            if params.get('files'):
                                files_text = f"• 【请求files】：\n{json_str(params.get('files'))}"
                            pre_text = f"• 【请求url】：\n{params.get('method')} {params.get('url')}\n• 【请求params】：\n{json_str(params.get('params'))}\n• 【请求header】：\n{json_str(params.get('headers'))}\n• 【请求cookies】：\n{json_str(params.get('cookies'))}\n{files_text}\n• 【请求body】：\n{pre_data}\n• 【响应结果】：\nHTTP CODE: {response.get('status')}\n{pre_result}"

        return Response({'code': 200, 'detail': '成功', 'data': {"pre_text": pre_text}}, status=status.HTTP_200_OK)


# 用例
class CaseModelViewSet(MyModelViewSet):
    queryset = Case.objects.all().select_related('project', 'creator')
    serializer_class = CaseModelSerializer
    # 需要过滤的查询条件数据
    filterset_fields = ('id', 'title', 'project__id', 'creator__username')
    pagination_class = MyPageNum
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(methods=['get'], detail=False)
    def steps(self, request, *args, **kwargs):
        case_id = request.query_params.get('id', None)
        api_ids = Case.objects.get(id=case_id).steps
        steps = []
        for api in api_ids:
            step = Api.objects.filter(pk__exact=api).values('id', 'title')
            if step:
                steps.append(step[0])
        return Response({'code': 200, 'detail': '成功', 'data': steps},
                        status=status.HTTP_200_OK)

    @action(methods=['delete'], detail=False)
    def batch_delete(self, request, *args, **kwargs):
        ids = request.query_params.get('ids', None)
        if not ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pks = ids.split(',')
        case = Case.objects.filter(pk__in=pks).filter(creator_id=self.request.user)
        del_id = list(case.values('id'))
        case.delete()
        return Response({'code': 200, 'detail': '成功', 'data': del_id},
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def run_case(self, request, *args, **kwargs):
        print_switch(True)
        params = request.data
        if isinstance(params['caseId'], list):
            for i in params['caseId']:
                t = threading.Thread(target=run_case, args=(i, self.request.user))
                t.start()
                t.join()
            return Response({'code': 200, 'detail': '成功', 'data': []},
                            status=status.HTTP_200_OK)
        else:
            info = run_case(params['caseId'], self.request.user)
            return Response({'code': info['code'], 'detail': info['msg'], 'data': {"report": info['report']}},
                            status=status.HTTP_200_OK)


# 报告
class ReportModelViewSet(MyModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportModelSerializer
    # 需要过滤的查询条件数据
    filterset_fields = ('case',)

    permission_classes = [permissions.IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user.username)

    def perform_destroy(self, instance):
        report_path = BASE_DIR / f"interface/reports/{instance}.html"
        report_path.unlink()
        instance.delete()

    @action(methods=['get'], detail=False)
    def get_detail(self, request, *args, **kwargs):
        return render(request, f'{request.GET.get("title")}.html')

    @action(methods=['delete'], detail=False)
    def batch_delete(self, request, *args, **kwargs):
        ids = request.query_params.get('ids', None)
        if not ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pks = ids.split(',')
        report = Report.objects.filter(pk__in=pks).filter(creator_id=self.request.user)
        del_id = list(report.values('id', 'title'))
        report.delete()
        from backends.settings import BASE_DIR
        for i in del_id:
            report_path = BASE_DIR / f"interface/reports/{i['title']}.html"
            report_path.unlink()
        return Response({'code': 200, 'detail': '成功', 'data': del_id},
                        status=status.HTTP_200_OK)


# 配置
class ConfigModelViewSet(MyModelViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigModelSerializer
    action_serializers = {
        'retrieve': ConfigDetailModelSerializer,
        'update': ConfigDetailModelSerializer,
        'partial_update': ConfigDetailModelSerializer,
        'create': ConfigDetailModelSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]

        return super(ConfigModelViewSet, self).get_serializer_class()

    filterset_fields = ['project__id']

    # permission_classes = [permissions.IsOwnerOrReadOnly]
    @action(methods=['get'], detail=False)
    def public_config(self, request, *args, **kwargs):
        data = Config.objects.filter(project_id__exact=None).values()
        return Response({'code': 200, 'detail': '成功', 'data': data},
                        status=status.HTTP_200_OK)


# 定时任务
class CrontabModelViewSet(MyModelViewSet):
    queryset = Crontab.objects.all()
    serializer_class = CrontabModelSerializer

    filterset_fields = ('id', 'name', 'creator__username')
    pagination_class = MyPageNum
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def create(self, request, *args, **kwargs):
        data = request.data
        args = data.get('args').split(',')
        args.append(self.request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        info = {'code': 200, 'detail': "成功"}
        try:
            scheduler.add_job(globals()[data['func']], data['trigger'], **ast.literal_eval(data['trigger_condition']),
                              id=str(serializer.data.get('id')),
                              args=args,
                              replace_existing=True)
            if not scheduler.running:
                scheduler.start()
        except Exception as e:
            print(e.__str__())
            info = {'code': 100, 'detail': e.__str__()}

        headers = self.get_success_headers(serializer.data)
        return Response({**info, 'data': serializer.data}, headers=headers,
                        status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            scheduler.remove_job(instance.id)
        except Exception as e:
            print(e.__str__())
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['delete'], detail=False)
    def batch_delete(self, request, *args, **kwargs):
        ids = request.query_params.get('ids', None)
        if not ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pks = ids.split(',')
        case = Crontab.objects.filter(pk__in=pks).filter(creator_id=self.request.user)
        del_id = list(case.values('id', 'name'))
        case.delete()
        for i in del_id:
            if scheduler.get_job(i['name']):
                # 如果存在相同的ID任务，先删掉
                scheduler.remove_job(i['name'])
        return Response({'code': 200, 'detail': '成功', 'data': del_id},
                        status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        trigger = instance.trigger
        trigger_condition = instance.trigger_condition
        data = request.data
        args = data.get('args').split(',')
        args.append(self.request.user)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        new_data = serializer.data
        info = {'code': 200, 'detail': "成功"}
        job = scheduler.get_job(data['id'])
        try:
            if job:
                job.modify(func=globals()[data['func']], args=args)
                if data['trigger'] != trigger or data['trigger_condition'] != trigger_condition:
                    print("变更定时期或者时间")
                    job.reschedule(data['trigger'], **ast.literal_eval(data['trigger_condition']))
                if data['job_state'] == 0:
                    job.pause()
                else:
                    job.resume()
            else:
                job = scheduler.add_job(globals()[data['func']], data['trigger'],
                                        **ast.literal_eval(data['trigger_condition']),
                                        id=str(data['id']),
                                        args=args,
                                        replace_existing=True)
                if not scheduler.running:
                    scheduler.start()
        # self.perform_update(serializer)
        except Exception as e:
            print(e.__str__())
            info = {'code': 100, 'detail': e.__str__()}

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response({**info, 'data': serializer.data},
                        headers=self.get_success_headers(serializer.data),
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def switch_job(self, request, *args, **kwargs):
        data = request.data
        job = Crontab.objects.get(id=data['id'])
        job_state = data['job_state']
        job.job_state = job_state
        scheduler_job = scheduler.get_job(data['id'])
        if scheduler_job and job_state == 1:
            scheduler_job.resume()
        if scheduler_job and job_state == 0:
            scheduler_job.pause()
        job.save()
        return Response({'code': 200, 'detail': "更新成功", 'data': []},
                        status=status.HTTP_200_OK)


# 文件列表
class FileModelViewSet(MyModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesModelSerializer

    def perform_create(self, serializer):
        name = serializer.validated_data['name']
        file = serializer.validated_data['file']
        instance = Files.objects.filter(name=name).first()
        if instance:
            instance.file.delete()
            instance.file = file
            instance.save()
        else:
            serializer.save()

    def perform_destroy(self, instance):
        instance.file.delete()
        instance.delete()


# 快捷方式列表
class TagModelViewSet(MyModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsModelSerializer
    pagination_class = MyPageNum
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(Tags.objects.filter(Q(creator=self.request.user) | Q(personal='2')))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'code': 200, 'detail': '成功', 'data': serializer.data},
                        status=status.HTTP_200_OK)


# 工具-Message
class ToolsMessageModelViewSet(MyModelViewSet):
    queryset = ToolsMessage.objects.all()
    serializer_class = ToolsMessageModelSerializer
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    # 获取验证码
    @action(methods=['post'], detail=False)
    def get_msg(self, request, *args, **kwargs):
        phone = request.data.get('phone', None)
        config = request.data.get('config', None)
        env = request.data.get('env', None)
        if not phone or not config:
            return Response(status=status.HTTP_404_NOT_FOUND)
        msg = get_msg(env, phone, config)
        return Response({'code': 200, 'detail': '成功', 'data': {'msg': msg}},
                        status=status.HTTP_200_OK)


xmind2testcase_start(1)
scheduler = ApschedulerJob().get_scheduler()

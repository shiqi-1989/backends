import ast
import asyncio
import json
import subprocess
import sys
import os
import threading
import time

import chardet
import httpx
import orjson
import requests
import urllib3
from backends.utils import fun_test
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from jsonpath import jsonpath
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from backends.settings import BASE_DIR, MEDIA_ROOT
# 自定义验证类(手机号和用户名)
from backends.utils import permissions
from .apscheduler_job import ApschedulerJob
from .serializer import *
from .test_run_case import run

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Create your views here.


#  获取simple jwt token
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh), str(refresh.access_token)


def get_now_time():
    """获取当前时间"""
    from django.utils import timezone
    # 返回时间格式的字符串
    now_time = timezone.now()
    now_time_str = now_time.strftime("%Y.%m.%d %H:%M:%S")
    print(now_time_str)

    # 返回datetime格式的时间
    # now_time = timezone.now().astimezone(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
    # now = datetime.datetime.strptime(now_time, '%Y-%m-%d %H:%M:%S')
    return now_time_str


def get_user_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
        print(f"真实ip：{ip}")
    else:
        ip = request.META.get('REMOTE_ADDR')
        print(f"代理ip：{ip}")

    return ip


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
        return Response({'code': 200, 'msg': '更新成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({'code': 200, 'msg': '创建成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({'code': 200, 'msg': '获取成功', 'data': response.data}, headers=response.headers,
                        status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({'code': 200, 'msg': '获取成功', 'data': response.data},
                        headers=response.headers,
                        status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({'code': 200, 'msg': '删除成功', 'data': response.data}, headers=response.headers,
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
        data = {"code": 200, "msg": "成功",
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
        return Response({'code': 200, 'msg': '成功', 'data': []},
                        status=status.HTTP_200_OK)


# 接口
class ApiModelViewSet(MyModelViewSet):
    # queryset = Api.objects.filter(~Q(project=None)).select_related('project')
    queryset = Api.objects.all().select_related('project')
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
        queryset = self.filter_queryset(Api.objects.filter(**filters))

        page = self.paginate_queryset(queryset)
        if page is not None:
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
        return Response({'code': 200, 'msg': '成功', 'data': api_data},
                        status=status.HTTP_200_OK)

    @action(methods=['delete'], detail=False)
    def batch_delete(self, request, *args, **kwargs):
        ids = request.query_params.get('ids', None)
        if not ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pks = ids.split(',')
        Api.objects.filter(pk__in=pks).filter(creator_id=self.request.user).delete()
        return Response({'code': 200, 'msg': '成功', 'data': []},
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
        start_time = int(round(time.time() * 1000))
        try:
            res = s.request(**params, verify=False, timeout=5)
            res.encoding = "utf-8"
            # res.raise_for_status()
            my_post_condition(res, postCondition, postConditionResult, config_id=config_id)
            # print(postConditionResult)
            return Response(
                {'code': 200, 'msg': '成功', "data": res.text, "postConditionResult": postConditionResult,
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
                {'code': 100, 'msg': '失败', "data": e.__str__(), "postConditionResult": postConditionResult,
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
                        Api.objects.filter(id=i['id']).update(response=response)
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

        return Response({'code': 200, 'msg': '成功', 'data': {"pre_text": pre_text}}, status=status.HTTP_200_OK)


# 用例
class CaseModelViewSet(MyModelViewSet):
    queryset = Case.objects.all().select_related('project')
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
        return Response({'code': 200, 'msg': '成功', 'data': steps},
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
        return Response({'code': 200, 'msg': '成功', 'data': del_id},
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
            return Response({'code': 200, 'msg': '成功', 'data': []},
                            status=status.HTTP_200_OK)
        else:
            info = run_case(params['caseId'], self.request.user)
            return Response({'code': info['code'], 'msg': info['msg'], 'data': {"report": info['report']}},
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
        return Response({'code': 200, 'msg': '成功', 'data': del_id},
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
        return Response({'code': 200, 'msg': '成功', 'data': data},
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
        info = {'code': 200, 'msg': "成功"}
        try:
            scheduler.add_job(globals()[data['func']], data['trigger'], **ast.literal_eval(data['trigger_condition']),
                              id=str(serializer.data.get('id')),
                              args=args,
                              replace_existing=True)
            if not scheduler.running:
                scheduler.start()
        except Exception as e:
            print(e.__str__())
            info = {'code': 100, 'msg': e.__str__()}

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
        return Response({'code': 200, 'msg': '成功', 'data': del_id},
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
        info = {'code': 200, 'msg': "成功"}
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
            info = {'code': 100, 'msg': e.__str__()}

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
        return Response({'code': 200, 'msg': "更新成功", 'data': []},
                        status=status.HTTP_200_OK)


# 文件列表
class FileModelViewSet(MyModelViewSet):
    queryset = Files.objects.all()
    serializer_class = FilesModelSerializer

    def perform_destroy(self, instance):
        file_path = MEDIA_ROOT / str(instance.file)
        file_path.unlink()
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
        return Response({'code': 200, 'msg': '成功', 'data': serializer.data},
                        status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def getAndroidDevices(self, request, *args, **kwargs):
        sh = run_cmd('adb devices')
        devices = read_sh(sh)
        result = devices.splitlines()
        devices_list = []
        for i in range(1, len(result)):
            dev_info = result[i]
            if '\tdevice' in dev_info:
                device = dev_info.split('\t')[0]
                product = get_manufacturer(device)
                devices_list.append({'value': device, 'label': product})
        return Response({'code': 200, 'msg': '获取成功！', 'data': devices_list},
                        status=status.HTTP_200_OK)


def get_dict(obj):
    new_dict = {}
    modified = ['If-None-Match', 'If-Modified-Since', 'Expires', 'Last-Modified']
    for i in obj:
        if i['selected'] and i['name']:
            if i['name'] in modified:
                new_dict.update({i['name']: ""})
            else:
                new_dict.update({i['name']: i['value']})
    return new_dict


def get_hosts(obj):
    hosts = []
    for i in obj:
        if i['selected'] and i['name']:
            hosts.append(i['value'])
    return hosts


def get_config(env):
    _config = {
        "host": "",
        "variables": {}
    }
    if env:
        config = Config.objects.get(id=env)
        _config['host'] = get_hosts(config.hosts)[0]
        _config['variables'] = get_dict(config.variables)
    return _config


def json_str(dic):
    return orjson.dumps(dic, option=orjson.OPT_INDENT_2).decode()


def get_request_data(data, config=None):
    def _replace(match):
        variable = match.group(1)
        if variable.startswith("__"):
            return eval(f'fun_test.{variable}')
        elif config:
            return str(config.get('variables').get(variable))

    data_str = orjson.dumps(data).decode()
    new_str = re.sub(r'\${(.*?)}', _replace, data_str)
    new_data = orjson.loads(new_str)
    if config: new_data['url'] = config.get('host') + new_data['url']

    # if config:
    #     data_str = orjson.dumps(data).decode()
    #     new_str = re.sub(r'\${(.*?)}', _replace, data_str)
    #     new_data = orjson.loads(new_str)
    #     new_data['url'] = config.get('host') + new_data['url']
    # else:
    #     new_data = data
    print(f"• 【请求url】：\n{new_data['method']} {new_data['url']}")
    params = get_dict(new_data['queryData'])
    print(
        f"• 【请求params】：\n{json_str(params)}")
    headers = get_dict(new_data['headersData'])
    print(
        f"• 【请求header】：\n{json_str(headers)}")
    cookies = get_dict(new_data['cookies'])
    print(
        f"• 【请求cookies】：\n{json_str(cookies)}")
    print(f"• 【请求body】：")
    data, files = {}, {}
    json_data = None
    if new_data['bodyType'] == 'x-www-form-urlencoded':
        data = get_dict(new_data['formUrlencodedData'])
        print(f"{json_str(data)}")
    elif new_data['bodyType'] == 'raw':
        json_data = orjson.loads(new_data['rawData']['text'])
        print(json_str(json_data))
    elif new_data['bodyType'] == 'form-data':
        if headers.get('Content-Type'):
            del headers['Content-Type']
        # data = {}
        # files = {}
        # files = []
        # for i in new_data['formData']:
        #     if i['name']:
        #         if i['type'] == 'file':
        #             for file in i['fileList']:
        #                 name = i['name']
        #                 file_name = file['response']['data']['name']
        #                 _type = file['raw']['type']
        #                 files.append((name, (file_name, open(FILES_ROOT / file_name, 'rb'), _type)))
        #         else:
        #             data[i['name']] = i['value']
        for i in new_data['formData']:
            if i['name']:
                if i['type'] == 'file':
                    for file in i['fileList']:
                        name = i['name']
                        file_name = file['response']['data']['name']
                        _type = file['raw']['type']
                        # with open(FILES_ROOT / file_name, 'rb') as f:
                        #     files[name] = (file_name, f.read(), _type)
                        files[name] = (file_name, open(FILES_ROOT / file_name, 'rb'), _type)
                else:
                    files[i['name']] = (None, i['value'])
        if files:
            print(files)
    return {
        "method": new_data['method'],
        "url": new_data['url'],
        "headers": headers,
        "params": params,
        "cookies": cookies,
        "data": data,
        "json": json_data,
        "files": files,
        "postCondition": new_data['postCondition']
    }


@xframe_options_exempt
def get_report(request, report_name=None):
    return render(request, f'{report_name}.html')


# 异步函数
async def req(client, params, obj_id, postCondition, postConditionResult):
    response, res = None, None
    start_time = int(round(time.time() * 1000))
    try:
        res = await client.request(**params)
        # res.raise_for_status()
        my_post_condition(res, postCondition, postConditionResult)
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
        print(e.__str__())
        err = "请求异常！"
        if e.__str__():
            err = e.__str__()
        if res:
            duration = int(res.elapsed.total_seconds() * 1000)
            _status = res.status_code
        else:
            duration = int(time.time() * 1000) - start_time
            _status = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = {
            "data": err,
            "postConditionResult": postConditionResult,
            "status": _status,
            "startTime": start_time,
            "duration": duration
        }
    finally:
        Api.objects.filter(id=obj_id).update(response=response)


# 异步调用 异步函数
async def main(obj_list):
    task_list = []  # 任务列表
    async with httpx.AsyncClient() as client:
        for obj in obj_list:
            config = None
            if obj.get('api_env'):
                config = get_config(obj.get('api_env'))
            params = get_request_data(obj, config)
            postConditionResult = []
            postCondition = params.pop('postCondition')
            res = req(client, params, obj['id'], postCondition, postConditionResult)
            task = asyncio.create_task(res)  # 创建任务
            task_list.append(task)
        await asyncio.wait(task_list)  # 收集任务


def my_assert(option, msg, actual, way, expected=None):
    # print(actual)
    # print(type(actual))
    #
    # print(expected)
    # print(type(expected))
    # msg["name"] = f"断言「{msg['name']}」:"
    try:
        if way == 0:
            assert actual == expected, f"实际:{actual}({type(actual)}), 预期:{expected}({type(expected)})"
            msg["content"] = f"实际:{actual}({type(actual)}), 预期:{expected}({type(expected)})"
            print(f"实际:{actual}({type(actual)}), 预期:{expected}({type(expected)})")
        if way == 1:
            assert actual != expected, f"实际:{actual}({type(actual)}), 预期:{expected}({type(expected)})"
            msg["content"] = f"实际:{actual}({type(actual)}), 预期:{expected}({type(expected)})"
        if way == 2:
            assert actual, f"实际:{actual}({type(actual)}), 预期: {True}({type(True)})"
            msg["content"] = f"实际:{actual}({type(actual)}), 预期: {True}({type(True)})"
        if way == 3:
            assert not actual, f"实际:{actual}({type(actual)}), 预期: {False}({type(False)})"
            msg["content"] = f"实际:{actual}({type(actual)}), 预期: {False}({type(False)})"
        if way == 4:
            assert actual in expected, f"实际:{actual}({type(actual)}) NOT IN 预期: {expected}({type(expected)})"
            msg["content"] = f"实际:{actual}({type(actual)}) IN 预期: {expected}({type(expected)})"
        if way == 5:
            assert actual not in expected, f"实际:{actual}({type(actual)}) IN 预期: {expected}({type(expected)})"
            msg["content"] = f"实际:{actual}({type(actual)}) NOT IN 预期: {expected}({type(expected)})"
        if way == 6:
            assert actual is None, f"实际:{actual}({type(actual)}) Is Not None"
            msg["content"] = f"实际:{actual}({type(actual)}) Is None"
        if way == 7:
            assert actual is not None, f"实际:{actual}({type(actual)}) Is None"
            msg["content"] = f"实际:{actual}({type(actual)}) Is Not None"
        # print("断言通过")
        # print(msg)
    except Exception as e:
        msg['content'] = f"AssertionError: {e}"
        msg['status'] = False
        # print(f"AssertionError：{e}")
        print("断言失败！")
        if option:
            raise


def my_post_condition(res, postCondition, postConditionResult, variables=None, option=None, config_id=None):
    print("后置操作".center(60, '*'))
    if variables is None:
        variables = {}
    for item in postCondition:
        if item['postConditionSwitch']:
            expression = item['expression']
            msg = {
                "status": True,
                "name": item["name"],
                "content": ""
            }
            if item['type'] == 0:
                msg["name"] = f"断言「{item['name']}」:"
                print(msg)
                print("• 【断言】:")
            if item['type'] == 1:
                msg["name"] = f"提取变量「{item['name']}」:"
                print("• 【提取变量】:")
            # 正则提取
            if item['resMetaData'] == 0:
                # print("正则提取")
                reg = re.compile(r"%s" % expression)
                actual_list = reg.findall(res.text)
                # print(f"正则结果： {actual_list}")
                if actual_list:
                    actual = actual_list[item['expressionIndex']]
                    # 断言
                    if item['type'] == 0:
                        expected = item['assert']['expected']
                        # print(f"预期结果值{expected} 类型 {type(expected)}")
                        expected = eval(f"{item['assert']['expectedType']}({repr(expected)})")
                        my_assert(option, msg, actual, item['assert']['way'], expected)
                    # 提取
                    if item['type'] == 1:
                        variables[item['name']] = actual
                        msg["content"] = f"{actual}"
                        print(f"{item['name']}:{actual}")
                else:
                    msg["status"] = False
                    msg["content"] = f"正则提取 {actual_list}"
                    print(f"正则提取失败: {expression}")
                    postConditionResult.append(msg)
                    continue

            #  json提取
            if item['resMetaData'] == 1:
                # print("Json提取")
                actual = jsonpath(res.json(), expression)
                if actual:
                    actual = actual[0]
                    if item['continueExtract']['is'] == 1:
                        separator = item['continueExtract']['separator']
                        index = item['continueExtract']['index']
                        try:
                            actual = re.split(f'[{separator}]', actual)[index]
                        except Exception as e:
                            print(f"Json提取失败：{e.__str__()}")
                            # msg["name"] = f"提取变量「{item['name']}」:"
                            msg["status"] = False
                            msg["content"] = f"继续提取变量值：{e.__str__()}"
                            postConditionResult.append(msg)
                            continue
                else:
                    # msg["name"] = f"提取变量「{item['name']}」:"
                    msg["status"] = False
                    msg["content"] = f"Json提取{actual}"
                    print(f"Json提取失败：{expression}")
                    postConditionResult.append(msg)
                    continue
                # print("最终结果")
                # print(actual)
                # 断言
                if item['type'] == 0:
                    # print(f"预期结果类型{item['assert']['expectedType']}")
                    expected = item['assert']['expected']
                    # print(f"预期结果值{expected} 类型 {type(expected)}")
                    expected = eval(f"{item['assert']['expectedType']}({repr(expected)})")
                    # print(expected)
                    my_assert(option, msg, actual, item['assert']['way'], expected)
                # 提取
                if item['type'] == 1:
                    variables[item['name']] = actual
                    # msg["name"] = f"提取变量「{item['name']}」:"
                    msg["content"] = f"{actual}"
                    if item.get('config'):
                        config_id = item['config']
                    if config_id:
                        _c = Config.objects.get(id=config_id)
                        _c_list = _c.variables
                        on_off = True
                        for i in _c_list:
                            if i['name'] == item['name']:
                                i['value'] = actual
                                on_off = False
                        if on_off:
                            _c_list.append({
                                "name": item['name'],
                                "value": actual,
                                "selected": True
                            })
                        _c.variables = _c_list
                        _c.is_active = True
                        _c.save()
                print(f"{item['name']}:{actual}")
            postConditionResult.append(msg)


def run_case(case_id, user=None):
    msg_info = {
        "report": None,
        "msg": "成功",
        "code": 200
    }
    case_info = Case.objects.get(id=case_id)
    obj_list = []
    # for api in case_info.steps:
    #     step = Api.objects.filter(pk__exact=api).values('title', 'method', 'url', 'bodyType', 'queryData',
    #                                                     'headersData', 'cookies', 'formData',
    #                                                     'formUrlencodedData',
    #                                                     'rawData', 'postCondition', 'api_env')
    #     if step:
    #         obj_list.append(step[0])
    obj_list = Api.objects.filter(pk__in=case_info.steps).values('title', 'method', 'url', 'bodyType', 'queryData',
                                                                 'headersData', 'cookies', 'formData',
                                                                 'formUrlencodedData',
                                                                 'rawData', 'postCondition', 'api_env')
    if not obj_list:
        msg_info['msg'] = '无可执行的有效步骤！'
        msg_info['code'] = 100
        return msg_info
    filters = {
        "project": case_info.project_id,
        "type": 0
    }
    g_config = get_dict(Config.objects.filter(**filters).first().variables)
    config = get_config(case_info.case_env)
    g_config.update(config['variables'])
    config['variables'] = g_config
    print(config)
    report_name = f"{case_info.title}-{int(time.time() * 1000)}"
    run(case_info.case_env, config, obj_list, name=report_name, title=case_info.title, description=case_info.info,
        tester=user)
    msg_info['report'] = f"http://{MY_HOST}:{MY_PORT}/interface/reportDetail/{report_name}"
    Report.objects.create(title=report_name, case=case_info, creator=user)
    return msg_info


###########  安卓共工具列表接口 ###########

def run_cmd(cmd):
    sh = subprocess.Popen(cmd,
                          shell=True,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    sh.stdin.close()
    return sh


def get_manufacturer(device):
    print(111111)
    print(device)
    sh = run_cmd(f'adb -s {device} shell getprop ro.product.manufacturer')
    sh2 = run_cmd(f'adb -s {device} shell getprop ro.product.model')
    manufacturer = read_sh(sh).replace(' ', '')
    model = read_sh(sh2).replace(' ', '-')
    return f'{manufacturer}_{model}'


def read_sh(sh):
    content = sh.stdout.read()
    sh.stdout.close()
    msg = None
    if content:
        encoding = chardet.detect(content)['encoding']
        msg = str(content, encoding=encoding).strip()
    return msg


# 定义一个开关函数
def print_switch(option):
    if option:
        sys.stdout = sys.__stdout__
    else:
        sys.stdout = open(os.devnull, 'w')


@xframe_options_exempt
def getAndroidDevices(request):
    sh = run_cmd('adb devices')
    devices = read_sh(sh)
    result = devices.splitlines()
    devices_list = []
    for i in range(1, len(result)):
        dev_info = result[i]
        if '\tdevice' in dev_info:
            device = dev_info.split('\t')[0]
            product = get_manufacturer(device)
            print(product)
            devices_list.append({product: device})
    return Response({'code': 200, 'msg': '获取成功！', 'data': {"devices": devices_list}},
                    status=status.HTTP_200_OK)


###########  安卓共工具列表接口 ###########
run_cmd("xmind2testcase webtool 5501")


#  Xmind 服务
class Xmind2case(APIView):
    permission_classes = [permissions.IsOwnerOrReadOnly]

    def get(self, request, *args, **kwargs):
        url = f"http://{MY_HOST}:{5501}/"
        return Response({'code': 200, 'msg': '成功', 'data': {'url': url}},
                        status=status.HTTP_200_OK)


class FunctionAssistant(MyModelViewSet):
    permission_classes = [permissions.IsOwnerOrReadOnly]

    @action(methods=['get'], detail=False)
    def fun_list(self, request, *args, **kwargs):
        fun_list = [x for x in dir(fun_test) if x.startswith('__') and not x.endswith("__")]
        fun_info = []
        for i in fun_list:
            fun_info.append({
                'name': i,
                'info': getattr(fun_test, i).__annotations__
            })

        return Response({'code': 200, 'msg': '成功', 'data': fun_list},
                        status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def fun_info(self, request, *args, **kwargs):
        func = request.query_params.get('func')
        fun_info = getattr(fun_test, func).__annotations__
        info_list = [{"name": key, "type": fun_info[key], "value": ""} for key in fun_info]
        return Response({'code': 200, 'msg': '成功', 'data': info_list},
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def fun_result(self, request, *args, **kwargs):
        func = request.data.get('func', None)
        if not func:
            return Response(status=status.HTTP_404_NOT_FOUND)
        result = None
        try:
            result = eval(f'fun_test.{func}')
        except Exception as e:
            raise ParamsException(e.__str__(), 403)
        return Response({'code': 200, 'msg': '成功', 'data': result},
                        status=status.HTTP_200_OK)


scheduler = ApschedulerJob().get_scheduler()
# print(scheduler.get_jobs())
# if not scheduler.get_jobs():
#     print(f"定时任务列表：{scheduler.get_jobs()},关闭服务")
#     if scheduler.running:
#         scheduler.shutdown()
# print(f"定时任务服务：{scheduler.running}")

import re

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from backends.settings import MY_HOST, MY_PORT
from .exception import ParamsException
from .models import *


# 注册
class UserSignupSerializer(serializers.ModelSerializer):
    mobile = serializers.CharField(default='')
    username = serializers.CharField(default=mobile)
    password = serializers.CharField(write_only=True, default='')

    class Meta:
        model = User
        fields = ['id', 'mobile', 'password', 'username']

    default_error_messages = {
        'code_error': '验证码不正确',
        'password_error': '两次密码输入不正确',
        "mobile_error": '手机号码格式不正确',
        "mobile_exists": '手机号码已注册',
        "username_exists": '用户名已存在',
    }

    def validate(self, attrs):
        if not re.match(r'^1[3-9]\d{9}$', attrs['mobile']):
            raise ParamsException(self.error_messages['mobile_error'], 200)
        if User.objects.filter(mobile=attrs.get('mobile')):
            raise ParamsException(self.error_messages['mobile_exists'], 200)
        if User.objects.filter(username=attrs.get('username')):
            raise ParamsException(self.error_messages['username_exists'], 200)

        attrs['password'] = make_password(attrs['password'])
        return attrs


# 登录
class UserSigninSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    mobile = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    default_error_messages = {
        'inactive_account': '账户已被禁用',
        'invalid_credentials': '账号或密码无效'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        self.user = authenticate(username=attrs.get("mobile"), password=attrs.get('password'))
        if self.user:
            if not self.user.is_active:
                raise ParamsException(self.error_messages['inactive_account'], 200)
            return attrs
        else:
            raise ParamsException(self.error_messages['invalid_credentials'], 200)


# 修改密码
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)


# 项目
class ProjectModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id', 'creator']


# 接口
class ApiModelSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.title')

    class Meta:
        model = Api
        # fields = '__all__'  # 设置全部字段自动生成
        fields = ['id', 'title', 'method', 'url', 'api_env', 'creator', 'project', 'project_name', 'response']
        read_only_fields = ['id', 'creator']


# 接口详情页
class ApiModelDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Api
        # fields = '__all__'  # 设置全部字段自动生成
        fields = ['id', 'title', 'method', 'url', 'bodyType', 'queryData', 'headersData', 'cookies',
                  'formData',
                  'formUrlencodedData', 'rawData', 'postCondition', 'response', 'project', 'api_env']
        read_only_fields = ['id', 'creator']


# 用例列表
class CaseModelSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.title')

    class Meta:
        model = Case
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id', 'creator']


# 报告列表
class ReportModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id', 'creator']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['url'] = f"http://{MY_HOST}:{MY_PORT}/interface/report/get_detail?title={data['title']}"
        return data


# 配置
class ConfigModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['id', 'type', 'title']  # 设置全部字段自动生成
        read_only_fields = ['id']


# 配置详情页
class ConfigDetailModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id']


# 定时任务
class CrontabModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crontab
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id', 'creator']


# 文件列表
class FilesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = '__all__'  # 设置全部字段自动生成


# 快捷方式列表
class TagsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id', 'creator']


# 工具-Message
class ToolsMessageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolsMessage
        fields = '__all__'  # 设置全部字段自动生成
        read_only_fields = ['id', 'creator']

from django.contrib.auth.models import AbstractUser
from django.db import models
from backends.settings import FILES_ROOT


# Create your models here.

class User(AbstractUser):
    mobile = models.CharField('手机号', max_length=11, unique=True, help_text='手机号',
                              error_messages={'unique': '此手机号码已注册'})

    #
    # # 只读属性
    # @property
    # def name(self):
    #     return self.nickname
    def __str__(self):
        return self.username

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        # 数据库表名
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


# 项目表
class Project(models.Model):
    """
    项目表
    """

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "project"
        verbose_name = "项目"
        verbose_name_plural = verbose_name

    title = models.CharField(max_length=30, blank=True, null=True, verbose_name="项目名称")
    info = models.CharField(max_length=1000, blank=True, default='', verbose_name="项目信息")
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")
    creat_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# 项目变量配置表
class Config(models.Model):
    """
    项目变量配置表
    """

    class Meta:
        # 默认id升序排序
        ordering = ['id']
        db_table = "config"
        verbose_name = "配置"
        verbose_name_plural = verbose_name

    choices = [('0', '全局变量'), ('1', "全局参数"), ('2', "环境配置")]
    title = models.CharField(max_length=30, blank=True, verbose_name="名称")
    hosts = models.JSONField(default=list, verbose_name="服务")
    variables = models.JSONField(default=list, verbose_name="变量")
    params = models.JSONField(default=list, verbose_name="参数")
    type = models.CharField(choices=choices, max_length=10)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, verbose_name="所属项目")
    creat_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# 接口表
class Api(models.Model):
    """
    接口库表
    """

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "api"
        verbose_name = "接口"
        verbose_name_plural = verbose_name

    title = models.CharField(max_length=30, blank=True, verbose_name="接口名称")
    method = models.CharField(max_length=10, verbose_name="method")
    url = models.TextField(blank=True, verbose_name="url")
    bodyType = models.CharField(max_length=30, verbose_name="数据类型")
    queryData = models.JSONField(default=list, verbose_name="params")
    headersData = models.JSONField(default=list, verbose_name="headers")
    cookies = models.JSONField(default=list, verbose_name="cookies")
    formData = models.JSONField(default=list, verbose_name="form-data")
    formUrlencodedData = models.JSONField(default=list, verbose_name="x-www-form-urlencoded")
    rawData = models.JSONField(default=dict, verbose_name="raw")
    postCondition = models.JSONField(default=list, verbose_name="后置条件")
    api_env = models.ForeignKey(Config, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL,
                                verbose_name="执行环境")
    status = models.CharField(max_length=5, blank=True, verbose_name="执行状态")
    creat_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属项目")
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")

    def __str__(self):
        return self.title


# 用例表
class Case(models.Model):
    """
    用例库表
    """

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "case"
        verbose_name = "用例"
        verbose_name_plural = verbose_name

    title = models.CharField(max_length=50, blank=True, null=True, verbose_name="用例名称")
    info = models.CharField(max_length=1000, blank=True, default='', verbose_name="用例信息")
    case_env = models.ForeignKey(Config, blank=True, null=True, db_constraint=False, on_delete=models.SET_NULL,
                                 verbose_name="执行环境")
    steps = models.JSONField(default=list, verbose_name="用例步骤")

    creat_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属项目")
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")

    def __str__(self):
        return self.title


# 报告表
class Report(models.Model):
    """
    用例报告表表
    """

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "report"
        verbose_name = "报告"
        verbose_name_plural = verbose_name

    title = models.CharField(max_length=100, blank=True, null=True, verbose_name="报告名称")
    case = models.ForeignKey(Case, null=True, blank=True, on_delete=models.CASCADE, verbose_name="所属用例")
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")
    creat_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# 定时任务表
class Crontab(models.Model):
    """
    定时任务表
    """

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "crontab"
        verbose_name = "定时任务"
        verbose_name_plural = verbose_name

    name = models.CharField(max_length=100, verbose_name="任务名称", unique=True)
    desc = models.CharField(max_length=255, blank=True, verbose_name="任务描述")
    func = models.CharField(max_length=255, blank=True, verbose_name="作业")
    func_type = models.IntegerField(blank=True, verbose_name="作业类型")
    args = models.CharField(max_length=255, blank=True, verbose_name="作业参数")
    kwargs = models.CharField(max_length=255, blank=True, verbose_name="作业关键字参数")
    trigger = models.CharField(max_length=25, default='date', verbose_name="触发器")
    trigger_condition = models.CharField(max_length=255, verbose_name="触发器条件")
    job_state = models.IntegerField(default=0, verbose_name="任务状态")
    creat_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")

    def __str__(self):
        return self.name


# 上传文件表
class Files(models.Model):
    name = models.CharField(max_length=100, default='', verbose_name='文件名称')
    file = models.FileField(upload_to='upload_files', verbose_name='文件路径')

    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "files"
        verbose_name = "文件列表"
        verbose_name_plural = verbose_name


# 快捷方式表
class Tags(models.Model):
    class Meta:
        # 默认id升序排序
        ordering = ['-id']
        db_table = "tags"
        verbose_name = "快捷方式列表"
        verbose_name_plural = verbose_name

    title = models.CharField(max_length=50, default='', verbose_name='快捷名称')
    link = models.TextField(default='', verbose_name='链接')
    color = models.CharField(max_length=100, default='', verbose_name='背景色')
    personal = models.CharField(max_length=5, default='2', verbose_name='是否私有-1：私有 2：共有')
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")

    def __str__(self):
        return self.title


# 工具-Message
class ToolsMessage(models.Model):
    class Meta:
        # 默认id升序排序
        ordering = ['id']
        db_table = "toolsMessage"
        verbose_name = "验证码工具"
        verbose_name_plural = verbose_name

    name = models.CharField(max_length=50, default='', verbose_name='端名称')
    src = models.TextField(blank=True, verbose_name='logo')
    config = models.JSONField(default=dict, verbose_name="配置")
    creator = models.ForeignKey(User, to_field='username', on_delete=models.DO_NOTHING, verbose_name="创建人")

    def __str__(self):
        return self.name

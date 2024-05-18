from django.contrib import admin
from interface.models import *


# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'mobile', 'gender')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator')


class ApiAdmin(admin.ModelAdmin):
    list_display = ('title', 'method', 'url', 'creator')


class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'case_env', 'project', 'creator')


class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator')


class TagsAdmin(admin.ModelAdmin):
    list_display = ('title', 'personal', 'creator')


class ConfigAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'project')


admin.site.register(User, UserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Api, ApiAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Crontab)
admin.site.register(Files)
admin.site.register(Tags, TagsAdmin)
admin.site.register(ToolsMessage)

from django.contrib import admin
from interface.models import *


# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'mobile', 'gender')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator')


admin.site.register(User, UserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Api)
admin.site.register(Case)
admin.site.register(Report)
admin.site.register(Config)
admin.site.register(Crontab)
admin.site.register(Files)
admin.site.register(Tags)
admin.site.register(ToolsMessage)

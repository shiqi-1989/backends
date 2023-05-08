from django.urls import path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from backends.utils import permissions

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Python API",
        default_version='v1',
        description="Welcome to the world of Tweet",
    ),
    public=True,
    permission_classes=(permissions.IsOwnerOrReadOnly,),
)

router = DefaultRouter(trailing_slash=False)
router.register('/project', views.ProjectModelViewSet, basename='/project')
router.register('/api', views.ApiModelViewSet, basename='/api')
router.register('/case', views.CaseModelViewSet, basename='/case')
router.register('/report', views.ReportModelViewSet, basename='/report')
router.register('/config', views.ConfigModelViewSet, basename='/config')
router.register('/crontab', views.CrontabModelViewSet, basename='/crontab')
router.register('/tag', views.TagModelViewSet, basename='/tag')
router.register('/upload_file', views.FileModelViewSet, basename='/upload_file')
router.register('/functionAssistant', views.FunctionAssistant, basename='/functionAssistant')
router.register('/toolsMessage', views.ToolsMessageModelViewSet, basename='/toolsMessage')

urlpatterns = [
                  re_path(r'^doc(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
                          name='schema-json'),  # 导出
                  path('/doc', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # <-- 美化UI
                  path('/redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # <-- 这里
                  # path('', include(router.urls)),
                  path('/register', views.UserSignupAPIView.as_view()),
                  path('/change_password', views.ChangePasswordAPIView.as_view()),
                  path('/refreshtoken', TokenRefreshView.as_view(), name='refresh'),
                  path('/login', views.UserSigninAPIView.as_view(), name="login"),
                  # re_path(r'^/reportDetail/(?P<report_name>.*)$', views.get_report),
                  # path('/getAndroidDevices', views.getAndroidDevices),
                  path('/main/', views.main),
                  path('/xmind2case', views.Xmind2case.as_view()),
                  # path('/functionAssistant', views.FunctionAssistant.as_view()),
                  # path('/logout', views.LogoutView.as_view())
              ] + router.urls

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """ 自定义权限只允许对象的所有者编辑它 """

    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求
        # 所以我们总是允许GET　HEAD POTIONS请求
        if request.method in permissions.SAFE_METHODS:
            return True
        # 只有该出版社的录入者才有权限写
        return obj.creator == request.user

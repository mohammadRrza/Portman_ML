from rest_framework import permissions
from classes.base_permissions import ADMIN, FILE_MANAGER_ADMIN, FILE_MANAGER_VIEWER, FTTH_CABLER, FTTH_INSTALLER, FTTH_OPERATOR, FTTH_ADMIN


class CanViewFileList(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'list':
            return request.user.type_contains([ADMIN, FILE_MANAGER_ADMIN, FILE_MANAGER_VIEWER])
        if view.action in ['upload', 'download']:
            return request.user.type_contains([ADMIN, FILE_MANAGER_ADMIN, FILE_MANAGER_VIEWER, FTTH_CABLER, FTTH_INSTALLER, FTTH_OPERATOR, FTTH_ADMIN])
        return request.user.type_contains([ADMIN, FILE_MANAGER_ADMIN])

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return request.user.type_contains([ADMIN, FILE_MANAGER_ADMIN, FILE_MANAGER_VIEWER])
        return request.user.type_contains([ADMIN, FILE_MANAGER_ADMIN])



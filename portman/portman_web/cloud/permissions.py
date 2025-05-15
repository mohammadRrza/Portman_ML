from rest_framework import permissions
from classes.base_permissions import ADMIN, CLOUD_ADMIN, CLOUD_VIEW


class CanViewDevicesList(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.type_contains([CLOUD_VIEW]):
            return request.method == 'GET'
        return request.user.type_contains([ADMIN, CLOUD_ADMIN])

    def has_object_permission(self, request, view, obj):
        return request.user.type_contains([ADMIN, CLOUD_ADMIN])


class ConfigRequestPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.type_contains([CLOUD_VIEW]):
            return request.method == 'GET'
        return request.user.type_contains([ADMIN, CLOUD_ADMIN])

    def has_object_permission(self, request, view, obj):
        if request.user.type_contains([CLOUD_VIEW]):
            return request.method == 'GET'
        return request.user.type_contains([ADMIN, CLOUD_ADMIN])

from rest_framework import permissions
from classes.base_permissions import ADMIN, SUPPORT, LTE_MAP_ADMIN


class CanViewMapPoints(permissions.BasePermission):
    def has_permission(self, request, view):
        can_write = request.user.type_contains([ADMIN, LTE_MAP_ADMIN])
        if request.user.type_contains([SUPPORT]):
            return can_write or request.method == 'GET'
        return can_write

    def has_object_permission(self, request, view, obj):
        can_write = request.user.type_contains([ADMIN, LTE_MAP_ADMIN])
        return can_write
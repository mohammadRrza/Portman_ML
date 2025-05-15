from rest_framework import permissions
from classes.base_permissions import ADMIN, TECHNICAL_PROFILE_ADMIN


class CanViewTechnicalProfileList(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.type_contains([ADMIN, TECHNICAL_PROFILE_ADMIN])

    def has_object_permission(self, request, view, obj):
        return request.user.type_contains([ADMIN, TECHNICAL_PROFILE_ADMIN])


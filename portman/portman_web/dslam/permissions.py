from rest_framework import permissions
from classes.base_permissions import ADMIN, RESELLER

class HasAccessToDslam(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.type_contains(ADMIN):
            return True
        elif view.action == 'list' and request.user.type_contains(RESELLER):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.type_contains(ADMIN):
            return True
        else:
            return False

class HasAccessToDslamPort(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.type_contains(RESELLER):
            if request.user.reseller.resellerport_set.filter(
                    port_name=obj.port_name,
                    dslam=obj.dslam,
            ).exists():
                return True
        else:
            return True

class HasAccessToDslamPortSnapshot(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.type_contains(RESELLER):
            if request.user.reseller.resellerport_set.filter(
                    port_name=obj.port_name,
                    dslam_id=obj.dslam_id,
            ).exists():
                return True
        else:
            return True

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user.type_contains(ADMIN)

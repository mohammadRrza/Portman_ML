from rest_framework import permissions
from classes.base_permissions import ADMIN, NOTIFICATION_ADMIN, BASIC

class UserManagement(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if view.action == 'retrieve':
            return True
        if request.user.has_permission('management_user'):
            return True
        if request.user == obj and not view.action == 'destroy':
            return True
        return False


class AccessManagement(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.type_contains([ADMIN]):
            return True
        allowed_functions = ['changepassword', 'login', 'ldap_login', 'SendResetPasswordLink', 'get_permission', 'stats',
                             'logout', 'markAsReadAllNotifications', 'list']
        return view.action in allowed_functions

    def has_object_permission(self, request, view, obj):
        return request.user.type_contains([ADMIN])


class NotificationManagement(permissions.BasePermission):

    def has_permission(self, request, view):
        isAdmin = request.user.type_contains([ADMIN, NOTIFICATION_ADMIN])
        if isAdmin:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        isAdmin = request.user.type_contains([ADMIN, NOTIFICATION_ADMIN])
        if isAdmin:
            return True
        return False

class ContactGroupPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        isAdmin = request.user.type_contains([ADMIN, NOTIFICATION_ADMIN])
        if isAdmin:
            return True
        return request.user.type_contains([BASIC]) == False

    def has_object_permission(self, request, view, obj):
        isAdmin = request.user.type_contains([ADMIN, NOTIFICATION_ADMIN])
        if isAdmin:
            return True
        return obj.creator == None or obj.creator.id == request.user.id


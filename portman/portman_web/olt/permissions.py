from rest_framework import permissions
from classes.base_permissions import ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_WEB_SERVICE, \
CONTRACTOR, FTTH_RESELLER, FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT


class CanViewObjectsList(permissions.BasePermission):
    def has_permission(self, request, view):
        if hasattr(view, 'action') and (view.action == 'list' or view.action == 'retrieve'):
            return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_RESELLER])
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT])

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_RESELLER])
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR])

class CanViewCableList(permissions.BasePermission):
    def has_permission(self, request, view):
        if hasattr(view, 'action') and (view.action == 'list' or view.action == 'retrieve'):
            return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT])
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT])

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT])
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR])

class CanViewOltList(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT])

    def has_object_permission(self, request, view, obj):
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT])


class CanViewFatList(permissions.BasePermission):

    def has_permission(self, request, view):
        read_actions = ['list', 'retrieve', 'download_excel', 'available_ports', 'relations']
        if hasattr(view, 'action') and view.action in read_actions:
            return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_WEB_SERVICE, FTTH_RESELLER])
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_WEB_SERVICE])
        # return request.user.type_contains([ADMIN, FTTH_ADMIN])

    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve', 'relations']:
            return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_WEB_SERVICE, FTTH_RESELLER])
        return request.user.type_contains([ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_SUPPORT, SUPPORT, FTTH_WEB_SERVICE])
        # return request.user.type_contains([ADMIN, FTTH_ADMIN])


class CanViewOltCommandList(CanViewOltList):
    pass


class CanViewOltTypeList(CanViewOltList):
    pass


class CanViewReservedPorts(permissions.BasePermission):
    def has_permission(self, request, view):
        if hasattr(view, 'action') and view.action in ['list', 'retrieve']:
            return request.user.type_contains(
                [ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_WEB_SERVICE, FTTH_RESELLER, FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT])
        if hasattr(view, 'action') and view.action in ['ready_to_install']:
            return request.user.type_contains(
                [ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_CABLER])
        if hasattr(view, 'action') and view.action in ['setup_ont', 'config_acs', 'complete_setup_info']:
            return request.user.type_contains(
                [ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_INSTALLER, FTTH_TECH_AGENT])
        return request.user.type_contains([FTTH_WEB_SERVICE, ADMIN, FTTH_ADMIN, FTTH_OPERATOR])

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return request.user.type_contains(
                [ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_WEB_SERVICE, FTTH_RESELLER, FTTH_INSTALLER, FTTH_TECH_AGENT, FTTH_CABLER])
        if hasattr(view, 'action') and view.action in ['ready_to_install']:
            return request.user.type_contains(
                [ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_CABLER])
        if hasattr(view, 'action') and view.action in ['setup_ont', 'config_acs', 'complete_setup_info']:
            return request.user.type_contains(
                [ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_INSTALLER, FTTH_TECH_AGENT])                
        return request.user.type_contains([FTTH_WEB_SERVICE, ADMIN, FTTH_ADMIN, FTTH_OPERATOR])

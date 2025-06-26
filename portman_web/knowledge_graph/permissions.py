from rest_framework import permissions
from classes.base_permissions import ADMIN, KNOWLEDGE_GRAPH_ADMIN, SUPPORT, SUPPORT_ADMIN


class KnowledgeGraphPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if hasattr(view, 'action') and (view.action in ['list', 'retrieve']):
            return request.user.type_contains(
                [ADMIN, KNOWLEDGE_GRAPH_ADMIN, SUPPORT, SUPPORT_ADMIN])
        return request.user.type_contains([ADMIN, KNOWLEDGE_GRAPH_ADMIN])

    def has_object_permission(self, request, view, obj):
        if hasattr(view, 'action') and (view.action in ['list', 'retrieve']):
            return request.user.type_contains(
                [ADMIN, KNOWLEDGE_GRAPH_ADMIN, SUPPORT, SUPPORT_ADMIN])
        return request.user.type_contains([ADMIN, KNOWLEDGE_GRAPH_ADMIN])

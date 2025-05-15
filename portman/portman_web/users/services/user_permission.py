from users.models import User, UserPermissionProfile, UserPermissionProfileObject
from django.contrib.contenttypes.models import ContentType


class UserPermissionService:

    def set_permission(self, object_ids, object_type, user_permission_profile):
        for object_id in object_ids:
            try:
                user_ppo = UserPermissionProfileObject()
                user_ppo.user_permission_profile = user_permission_profile
                user_ppo.content_type = ContentType.objects.get(model=object_type)
                user_ppo.object_id = object_id
                user_ppo.save()
            except:
                continue

    def set_user_permission_profile(self, user, permission_profile, action='allow', is_active=True):
        instance = UserPermissionProfile.objects.create(user=user, action=action,
                                                        permission_profile=permission_profile, is_active=is_active)
        return instance

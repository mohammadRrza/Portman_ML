from dj_bridge import AuthGroup, User, AuthPermission
if __name__ == '__main__':
    allUsers = User.objects.all()
    for user in allUsers:
        userTypes = user.type.split(",")
        groups = AuthGroup.objects.filter(name__in=userTypes).values_list('id', flat=True)
        print(userTypes, groups)
        user.groups.set(groups)

    # groupAdmin = AuthGroup.objects.filter(name="ADMIN").get()
    # print(groupAdmin)
    # groupAdmin.permissions.set(AuthPermission.objects.all())
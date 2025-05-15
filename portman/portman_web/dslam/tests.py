#from django.test import TestCase
from unittest import TestCase
from users.models import User
from classes.base_permissions import ADMIN, SUPPORT, DIRECTRESELLER

class CheckPermissionsTestCase(TestCase):
    def setUp(self):
        pass

    def type_contains(self,type, types):
        print("isinstance >> ", isinstance(types, str))
        if isinstance(types, str):
            types = [types]

        print("TO .. CHECK TYPES", types)
        userTypes = type.replace(" ", "").split(",")
        print("USER TYPES", userTypes)
        for type in types:
            print("for type", type)
            if type in userTypes:
                return True
        return False

    def ldap_groups_contains(self, ldap_group_name, groups):
        print("groups : isinstance >> ", isinstance(groups, str))
        if isinstance(groups, str):
            groups = [groups] 

        print("TO .. CHECK GROUPS", groups)
        userLdapGroups = ldap_group_name.replace(" ", "").split(",")
        print("USER GROUPS", userLdapGroups)
        for group in groups:
            if group in userLdapGroups:
                return True
        return False        

    def test_function(self):
        has = self.type_contains('RESELLER-ADMIN', 'ADMIN')
        print(has, "HHHHHHHHAAAAAAASSSSSSS")
        self.assertIs(has, False)
        has = self.ldap_groups_contains('Portman-Support, FTTH', 'Portman-support')
        self.assertIs(has, False)

    def test_admin_permission(self):
        username = 'a.almasi'
        ldap_login = 'false'

        if username and ldap_login == 'false':
            user = User.objects.filter(username=username).first()
            print(user.type, user.type_contains(ADMIN), ADMIN, 'CHECKING USER TYPE')
            if user and user.type_contains(ADMIN) == False:
                print(user, 'USER +FOUND')
                user_id = user.id
                # model_user = User(type=user.type)
                # model_user.set_user_id(user_id)
                allowed_dslams = user.get_allowed_dslams()
                print('USER TYPE IS ' + user.type)
                print("LDAP CHECK", user.ldap_groups_contains('Portman-support'))
                if user.type_contains([SUPPORT, DIRECTRESELLER]):
                    print('USER TYPE IS ' + user.type)
                    print('ALLOWED DSLAMS :', allowed_dslams)
        
import ldap, os
from .models import User
from classes.base_permissions import BASIC
from django.contrib.auth.models import Group as AuthGroup

PORTMAN_ENV = os.environ.get('PORTMAN_ENV', 'prod')

LDAP_SERVER = 'ldap://dc.pishgaman.local:389'
if PORTMAN_ENV != 'prod':
    LDAP_SERVER = 'ldap://172.28.238.238:389'

LDAP_BASE = "DC=pishgaman,DC=local"


def ldap_auth(username, password):
    conn = ldap.initialize(LDAP_SERVER)
    try:
        conn.protocol_version = ldap.VERSION3
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.simple_bind_s(username + '@pishgaman.local', password)
        logon_name = conn.whoami_s().split('\\')[1]
        search_filter = f"(sAMAccountName={logon_name})"
        retrieve_attributes = ['memberOf', 'cn', 'mail']
        search_res = conn.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, search_filter, retrieve_attributes)
        result_obj = search_res[0][1]
        email = result_obj.get('mail')[0].decode('utf-8')
        fullname = result_obj.get('cn')[0].decode('utf-8')
        if result_obj.get('memberOf'):
            group_info = [value.decode('utf-8') for value in result_obj.get('memberOf')]
            group_name = [gp.split(",")[0].split("=")[1] for gp in group_info]
        else:
            group_name = []
            #return dict(message="you are not belongs to any LDAP group!")

        try:
            user = is_user_exist(email.lower())
            if not user:
                params = dict(first_name=fullname.split()[0],
                            last_name=fullname.split()[-1],
                            username=email.split('@')[0].lower(), national_code=username,
                            email=email.lower(), ldap_groups=group_name)
                create_user(params)
            else:
                update_group_name(user, group_name)
        except Exception as uge:
            print("Error on user group action", uge)
            pass

    except ldap.LDAPError as e:
        return dict(message="Failed to authenticate")

    conn.unbind_s()
    return dict(message="Success", fullname=fullname, email=email, group_name=group_name, logon_name=logon_name)


def is_user_exist(email):
    return User.objects.filter(email__iexact=email).first()


def update_group_name(user, group_names):
    user.ldap_group_name = ','.join(group_names)
    user.save()


def create_user(params):
    user = User.objects.create_user(password='miladS9$#', is_superuser=False, username=params['username'],
                             first_name=params['first_name'], last_name=params['last_name'], email=params['email'],
                             ldap_group_name=','.join(params['ldap_groups']), national_code=params['national_code'],
                             is_staff=False, is_active=True, type=BASIC, tel='', is_notifiable=False, mobile_number='')
    if user:
        basicGroup = AuthGroup.objects.filter(name=BASIC).values_list('id', flat=True)
        basicGroup and user.groups.set(basicGroup)

    return user


if __name__ == "__main__":
    # user = ldap_auth('0422094080@pishgaman.local', '{PASS}')
    print('MAIN')


import os
import sys

from django.utils.translation import gettext_lazy as _
from django.core.serializers import serialize
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model

from rest_framework import viewsets, status, views, mixins, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError

from users.serializers import *
from users.models import (UserAuditLog, PortmanLog, UserPermissionProfile, UserPermissionProfileObject, ContactGroup,
                          ContactGroupIndex, NotificationLog, PermissionProfile, GroupInfo)
from users.mail import Mail
from dslam.models import Command
from django.http import JsonResponse, HttpResponse
import simplejson as json
from khayyam import *
from datetime import date, datetime, timedelta

from dslam.views import LargeResultsSetPagination

# from portman_web.users.backends import ldap_auth
from .backends import ldap_auth
from .serializers import PortmanLogSerializer, ShowNotificationLogSerializer, ProvinceAccessSerializer
from .models import ProvinceAccess
from dslam.models import Command
from .services.mini_services import send_message, save_notif_log
from .services.user_permission import UserPermissionService
from rest_framework import pagination
from django.db import transaction
from .permissions.user_permissions import AccessManagement, NotificationManagement, ContactGroupPermission
from django.contrib.auth.models import Group as AuthGroup
from django.db.models import Q
from classes.base_permissions import ADMIN, FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT
from config.settings import MOBILE_APP_VERSION

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    Get users
    ---
    parameters:
        - username:
            type: string
            paramType: form
            required: true
        - sort_field:
            type: string
            paramType: form
            required: true
    """
    model = User
    permission_classes = (IsAuthenticated, AccessManagement)
    serializer_class = UserSerializer
    queryset = User.objects.all().order_by('-id')

    def get_queryset(self):
        queryset = self.queryset
        searchPhrase = self.request.query_params.get('search_phrase', None)
        username = self.request.query_params.get('username', None)
        first_name = self.request.query_params.get('first_name', None)
        last_name = self.request.query_params.get('last_name', None)
        user_type = self.request.query_params.get('type', None)
        sort_field = self.request.query_params.get('sort_field', None)
        is_notifiable = self.request.query_params.get('is_notifiable', None)
        page_size = self.request.query_params.get('page_size', 10000)
        if username:
            queryset = queryset.filter(username__icontains=username)

        if first_name:
            queryset = queryset.filter(first_name__istartswith=first_name)

        if last_name:
            queryset = queryset.filter(last_name__istartswith=last_name)

        if user_type:
            queryset = queryset.filter(type=user_type)

        if searchPhrase:
            searchForEmail = Q(email__icontains=searchPhrase)
            searchForFirstName = Q(first_name__icontains=searchPhrase)
            searchForLastName = Q(last_name__icontains=searchPhrase)
            searchForFaFirstName = Q(fa_first_name__icontains=searchPhrase)
            searchForFaLastName = Q(fa_last_name__icontains=searchPhrase)
            queryset = queryset.filter(searchForEmail | searchForFirstName | searchForLastName | searchForFaFirstName | searchForFaLastName)

        if sort_field:
            queryset = queryset.order_by(sort_field)

        if is_notifiable == 'true' or is_notifiable == 'True':
            queryset = queryset.filter(is_notifiable=True)

        if not self.request.user.is_superuser:
            queryset = queryset.exclude(Q(is_superuser=True) | Q(groups__name=ADMIN))

        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request):
        data = request.data
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            new_user = serializer.save()
            # add_audit_log(
            #    request,
            #    'user',
            #    'create',
            #    object_id=new_user.pk,
            #    description='create user %s'%new_user.username,
            # )
            # save limit ips if exists
            new_user.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        """
         Update user
        """

        user = self.get_object()
        data = request.data

        serializer = UserUpdateSerializer(instance=user, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def changepassword(self, request, pk=None):
        """
        Change Password
        ---
        parameters:
            - new_password:
                type: string
                paramType: form
                required: true
        """
        user = self.get_object()
        data = request.data

        serializer = ChangePasswordSerializer(instance=user, data=data)
        if serializer.is_valid():
            user.set_password(data['new_password'])
            user.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False, permission_classes=[], authentication_classes=[])
    def login(self, request):
        """
        Login User
        ---
        parameters:
            - username:
                type: string
                paramType: form
                required: true
            - password:
                type: string
                paramType: form
                required: true
        """

        try:
            data = request.data
            username = data.get('username', '')
            password = data.get('password', '')

            # Try LDAP login first
            user = ldap_auth(username=username, password=password)
            if user['message'] == "Success":
                portmanUser = User.objects.filter(email__iexact=user['email']).first()
                if portmanUser:
                    if portmanUser.national_code is None:
                        portmanUser.national_code = user.get('logon_name', None)
                        portmanUser.save()
                    login(request, portmanUser)
            elif 'not belongs' in user['message']:
                return Response({'error': _('You are not belongs to any LDAP group!')},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Try regular login if LDAP login fails
                portmanUser = authenticate(username=username, password=password)
            
            if portmanUser is not None:
                if portmanUser.is_active:
                    login(request, portmanUser)

                    # create token
                    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
                    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
                    payload = jwt_payload_handler(portmanUser)
                    if portmanUser.email == 'pishgaman.note@pishgaman.net':
                        payload['exp'] = datetime.utcnow() + timedelta(days=90)
                    token = jwt_encode_handler(payload)

                    response = serializer = UserSerializer(portmanUser).data
                    response['token'] = token
                    response['mobile_app_version'] = MOBILE_APP_VERSION

                    return Response(response, status=status.HTTP_200_OK)
                else:
                    return Response({'error': _('User inactive or deleted.')}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'error': _('Invalid username/password.')}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'error': _('Error is {0}').format(ex), 'Line': str(exc_tb.tb_lineno)})

    @action(methods=['POST'], detail=False, permission_classes=[], authentication_classes=[])
    def SendResetPasswordLink(self, request):
        try:
            user_mail = request.data.get('email')
            mail_info = Mail()
            mail_info.from_addr = 'oss-problems@pishgaman.net'
            mail_info.to_addr = user_mail
            mail_info.msg_body = 'eeeeeeeeeeeessssssssssssss'
            mail_info.msg_subject = 'Reset Your OSS Passwd'
            Mail.Send_Mail(mail_info)
            return JsonResponse(
                {'row': "ddddd"})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return Response({'message': str(ex) + "  // " + str(exc_tb.tb_lineno)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['GET'], detail=False)
    def get_permission(self, request):
        user = request.user
        data = request.data
        pp_list = UserPermissionProfile.objects.filter(user__username=user.username).values_list('permission_profile',
                                                                                                 flat=True)
        permissions = PermissionProfilePermission.objects.filter(permission_profile__in=pp_list).values_list(
            'permission__codename', flat=True)
        return Response({'permissions': permissions,
         'user_type': user.type, 
         'user_info': dict(name=user.first_name + ' ' +user.last_name, username=user.username, mail=user.email),
         'groups' : user.groups.values_list('name', flat=True)
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def logout(self, request):
        """
        Logout User
        """
        refresh_jwt_token(request)
        logout(request)
        return Response({}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'])
    def permissions(self, request,  pk=None):
        user = self.get_object()

        if request.method == 'GET':
            permission_serializer = UserPermissionSerializer(user, many=False)
            return Response(permission_serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            user = self.get_object()
            data = request.data
            objects = data.get('objects')
            upp = data.get('user_permission_profile')
            upp = UserPermissionProfile.objects.get(id=upp)
            user_permission = UserPermissionService()
            with transaction.atomic():
                if objects:
                    for obj in objects:
                        ids = obj.get('ids', [])
                        object_type = obj.get('type')
                        UserPermissionProfileObject.objects.filter(user_permission_profile=upp,
                                                                   content_type__model=object_type).delete()
                        user_permission.set_permission(object_ids=ids, object_type=object_type, user_permission_profile=upp)
                permission_serializer = UserPermissionSerializer(user, many=False)
                return Response(permission_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def types(self, request):
        allTypes = GroupInfo.objects.all()
        types = []
        for type in allTypes:
            types.append(dict(id=type.pk, name=type.name, title=type.title))
        return Response(dict(results=types), status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='update-type')
    def update_type(self, request, pk=None):
        user = self.get_object()
        types = request.data.get('types', None)
        if types:
            types = types.replace(" ", "")
            user.type = types
            user.groups.set(AuthGroup.objects.filter(name__in=types.split(",")).values_list('id', flat=True))
            user.save()
            return Response({'message': _('User type updated successfully.')}, status=status.HTTP_200_OK)
        else:
            return Response({'error': _('No types provided.')}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='set-bulk-permissions')
    def set_bulk_permission(self, request, pk=None):
        users_permission_profile = request.data.get('users_permission_profile', None)
        objects = request.data.get('objects', None)
        if not users_permission_profile:
            return Response({'error': _('No users permission profile provided.')}, status=status.HTTP_400_BAD_REQUEST)

        users_permission_profile = UserPermissionProfile.objects.filter(id__in=users_permission_profile)
        for user_permission_profile in users_permission_profile:
            user_permission = UserPermissionService()
            with transaction.atomic():
                if objects:
                    for obj in objects:
                        ids = obj.get('ids', [])
                        object_type = obj.get('type')
                        UserPermissionProfileObject.objects.filter(user_permission_profile=user_permission_profile,
                                                                   content_type__model=object_type).delete()
                        user_permission.set_permission(object_ids=ids, object_type=object_type,
                                                       user_permission_profile=user_permission_profile)
        return Response(dict(results=_('Permissions assignment successfully.')), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='set-bulk-profile')
    def set_bulk_profile(self, request, pk=None):
        user_ids = request.data.get('user_ids', None)
        permission_profile = request.data.get('permission_profile', None)
        is_active = request.data.get('is_active', True)
        action = request.data.get('action', 'allow')
        users = User.objects.filter(id__in=user_ids)
        permission_profile = PermissionProfile.objects.get(id=permission_profile)
        users_permission_profile = []
        for user in users:
            user_permission = UserPermissionService()
            users_permission_profile.append(user_permission.set_user_permission_profile(user=user,
                                                                                        permission_profile=permission_profile,
                                                                                        action=action,
                                                                                        is_active=is_active))

        return Response(UserPermissionProfileSerializer(users_permission_profile, many=True).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        notifications = NotificationLog.objects.filter(receiver=request.user, read_at__isnull=True, send_type='in_app').order_by('-date')
        return Response({
            'results' : {
                'unread_notifications_count': notifications.count(),
                'unread_notifications': ShowNotificationLogSerializer(notifications.all()[0:5], many=True).data
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark-notifications-as-read')
    def markAsReadAllNotifications(self, request):
        notifications = NotificationLog.objects.filter(receiver=request.user, read_at__isnull=True, send_type='in_app')
        notifications.update(read_at=datetime.now())
        return Response({
            'results' : {
            }
        }, status=status.HTTP_200_OK)







class UserAuditLogViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = UserAuditLogSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = UserAuditLog.objects.all()
        data = self.request.query_params
        keywords = data.get('search_keywords')
        action = data.get('search_action')
        ip = data.get('search_ip')
        username = data.get('search_username')
        start_date = data.get('search_date_from')
        end_date = data.get('search_date_to')
        sort_field = data.get('sort_field')

        if keywords:
            keyword_params = keywords.split(',')
            for keyword in keyword_params:
                print(keyword)
                queryset = queryset.filter(description__icontains=keyword)

        if ip:
            queryset = queryset.filter(ip=ip)

        if action:
            queryset = queryset.filter(action=action)

        if username:
            queryset = queryset.filter(username=username)

        if start_date:
            # for example start_date = 20120505 and end_date = 20120606
            year, month, day = start_date.split('/')
            start_date = JalaliDate(year, month, day).todate()
            if end_date:
                year, month, day = end_date.split('/')
                end_date = JalaliDate(year, month, day).todate()
            else:
                end_date = date.today()

            queryset = queryset.filter(created_at__gte=start_date, created_at__lt=end_date).order_by('created_at')

        if sort_field:
            queryset = queryset.order_by(sort_field)

        return queryset

    @action(methods=['GET'], detail=False)
    def actions(self, request):
        data = tuple(enumerate(UserAuditLog.objects.values_list('action').order_by().distinct(), 1))
        data_dict = [{'id': key, 'text': value} for key, value in data]
        return HttpResponse(json.dumps(data_dict), content_type='application/json; charset=UTF-8')


class PermissionViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = PermissionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Permission.objects.all()
        title = self.request.query_params.get('search_title', None)
        if title:
            queryset = queryset.filter(title__istartswith=title)

        return queryset

    @action(methods=['GET'], detail=False)
    def get_user_permissions(self, request):
        user = request.user
        data = request.query_params
        username = data.get('username')
        permissions = []
        if username:
            pp_list = UserPermissionProfile.objects.filter(user__username=username).values_list('permission_profile',
                                                                                                flat=True)
            permissions = PermissionProfilePermission.objects.filter(permission_profile__in=pp_list).values_list(
                'permission__codename', flat=True)
        return Response({'results': permissions})


class PermissionProfileViewSet(mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    serializer_class = PermissionProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = PermissionProfile.objects.all()
        name = self.request.query_params.get('name', None)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size

        if name:
            queryset = queryset.filter(name__istartswith=name)

        return queryset.order_by('-id')

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionProfilePermissionViewSet(mixins.ListModelMixin,
                                         mixins.CreateModelMixin,
                                         mixins.RetrieveModelMixin,
                                         mixins.UpdateModelMixin,
                                         mixins.DestroyModelMixin,
                                         viewsets.GenericViewSet):
    serializer_class = PermissionProfilePermissionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = PermissionProfilePermission.objects.all()
        return queryset

    @action(methods=['POST'], detail=False)
    def delete_permission_profile(self, request):
        user = request.user
        data = request.data
        permission_profile_id = data.get('permission_profile_id')
        perofile_profile = PermissionProfile.objects.get(id=permission_profile_id)
        PermissionProfilePermission.objects.filter(permission_profile=perofile_profile).delete()
        perofile_profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        data = request.data

        permission_profile_obj, permission_profile_created = PermissionProfile.objects.get_or_create(
            name=data.get('permission_profile_name'))
        if not permission_profile_created:
            return Response({'result': 'Permission Profile Name is exist !!!.'}, status=status.HTTP_400_BAD_REQUEST)

        permissions_obj = Permission.objects.filter(id__in=data.get('permissions'))

        for permission_obj in permissions_obj:
            ppp = PermissionProfilePermission()
            ppp.permission_profile = permission_profile_obj
            ppp.permission = permission_obj
            ppp.save()

            # description = u'Create Permission Profile Name: {0}'.format(permission_profile_obj.name)
            # add_audit_log(request, 'PermissionProfile', permission_profile_obj.id, 'Create Permission Profile', description)

        return Response('Permissions Profile created', status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data
        permission_profile_obj = PermissionProfile.objects.get(id=data.get('permission_profile_id'))
        permissions = data.get('permissions')
        PermissionProfilePermission.objects.filter(permission_profile=permission_profile_obj).delete()
        permissions_obj = Permission.objects.filter(id__in=permissions)

        for permission_obj in permissions_obj:
            ppp = PermissionProfilePermission()
            ppp.permission_profile = permission_profile_obj
            ppp.permission = permission_obj
            ppp.save()

        return Response('Permissions Profile updated', status=status.HTTP_204_NO_CONTENT)


class UserPermissionProfileViewSet(mixins.ListModelMixin,
                                   mixins.CreateModelMixin,
                                   mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   viewsets.GenericViewSet):
    serializer_class = UserPermissionProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = UserPermissionProfile.objects.all()
        username = self.request.query_params.get('username', None)
        user_id = self.request.query_params.get('user_id', None)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size
        if username:
            queryset = UserPermissionProfile.objects.select_related('user').filter(user__username__icontains=username)
        if user_id:
            queryset = queryset.filter(user__id=user_id)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PortmanLogAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        data = request.data
        queryset = PortmanLog.objects.all()
        username = data.get('username', None)
        command = data.get('command', None)
        request = data.get('request', None)
        response = data.get('response', None)
        log_date = data.get('log_date', None)
        source_ip = data.get('source_ip', None)
        method_name = data.get('method_name', None)
        status = data.get('status', None)
        exception_result = data.get('exception_result', None)
        try:
            if username:
                queryset = queryset.filter(username__icontains=username)

            if command:
                queryset = queryset.filter(command__icontains=command)

            if request:
                queryset = queryset.filter(request__icontains=request)

            if response:
                queryset = queryset.filter(response__icontains=response)

            if log_date:
                queryset = queryset.filter(log_date__icontains=log_date)

            if source_ip:
                queryset = queryset.filter(source_ip__icontains=source_ip)

            if method_name:
                queryset = queryset.filter(method_name__icontains=method_name)

            if status:
                queryset = queryset.filter(method_name__icontains=status)

            if exception_result:
                queryset = queryset.filter(method_name__icontains=exception_result)

            result = serialize('json', queryset)
            return HttpResponse(result, content_type='application/json')

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class PortmanLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = PortmanLog.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = PortmanLogSerializer

    @action(methods=['GET'], detail=False)
    def get_queryset(self):
        queryset = self.queryset
        request = self.request.query_params.get('request', None)
        username = self.request.query_params.get('username', None)
        command = self.request.query_params.get('command', None)
        response = self.request.query_params.get('response', None)
        log_date = self.request.query_params.get('log_date', None)
        source_ip = self.request.query_params.get('source_ip', None)
        method_name = self.request.query_params.get('method_name', None)
        status = self.request.query_params.get('status', None)
        exception_result = self.request.query_params.get('exception_result', None)
        reseller_name = self.request.query_params.get('reseller_name', None)

        try:
            if request:
                queryset = queryset.filter(request__icontains=request)

            if username:
                queryset = queryset.filter(username__icontains=username)

            if command:
                queryset = queryset.filter(command__icontains=command)

            if response:
                queryset = queryset.filter(response__icontains=response)

            if log_date:
                queryset = queryset.filter(log_date__icontains=log_date)

            if source_ip:
                queryset = queryset.filter(source_ip__icontains=source_ip)

            if method_name:
                queryset = queryset.filter(method_name__icontains=method_name)

            if status:
                queryset = queryset.filter(status__icontains=status)

            if exception_result:
                queryset = queryset.filter(exception_result__icontains=exception_result)

            if reseller_name:
                queryset = queryset.filter(reseller_name__icontains=reseller_name)

            # result = serialize('json', queryset)
            # return HttpResponse(result, content_type='application/json')
            return queryset

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetUserPermissionProfileObjectsAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            permission_objects = []
            dslam_perm = {}
            username = request.GET.get('username', None)
            user_id = User.objects.get(username=username).id
            user_profile_id = UserPermissionProfile.objects.get(user_id=user_id).permission_profile_id
            uppo_list = UserPermissionProfileObject.objects.filter(user_permission_profile__id=user_profile_id).values()
            for item in list(uppo_list):
                if item['content_type_id'] == 7:
                    permission_objects.append(str(item['object_id']) + 'Dslam')
                elif item['content_type_id'] == 16:
                    permission_objects.append(str(item['object_id']) + 'Command')
            print(uppo_list)
            return JsonResponse({'row': permission_objects})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class SetPermissionForUserAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        mail_info = Mail()
        mail_info.from_addr = 'oss-problems@pishgaman.net'
        mail_info.to_addr = 'm.taher@pishgaman.net'
        mail_info.msg_body = 'Portman Mail Test'
        mail_info.msg_subject = 'Portman_Mail_Test'
        Mail.Send_Mail_With_Attachment(mail_info)
        try:
            email = request.GET.get('email', None)

            result = set_permission_for_user(email)
            return JsonResponse({'result': result})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class SetBulkPermissionByPermissionProfileId(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request, fname=None):
        try:
            date = request.data
            profiles_id = date.get('profiles_id', None)
            commands = date.get('commands', None)
            result = set_permission_by_permission_profile_id(profiles_id, commands)
            return JsonResponse({'result': result})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class SetBulkPermissionForUserApiView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request):
        try:
            data = request.data
            emails = data.get('emails', None)
            commands = data.get('commands', None)
            result = set_bulk_permission_for_user(emails, commands)
            return JsonResponse({'result': result})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


def set_permission_by_permission_profile_id(profiles_id, commands):
    try:
        commands_id = []
        users_profile_id = []
        wrong_id = []

        for item in profiles_id:
            query_set = UserPermissionProfile.objects.filter(permission_profile_id=item)
            if query_set.exists():
                for obj in query_set:
                    users_profile_id.append(obj.id)
            else:
                wrong_id.append(item)

        for item in commands:
            commands_id.append(Command.objects.get(text=item).id)

        for item in users_profile_id:
            for command in commands_id:
                try:
                    UserPermissionProfileObject.objects.create(object_id=command, content_type_id=16,
                                                               user_permission_profile_id=item)
                except Exception as ex:
                    if "duplicate key value violates unique" in str(ex):
                        continue
                    else:
                        return str(ex)
        if len(wrong_id) == 0:
            return "Specified commands successfully added."
        else:
            if len(users_profile_id) != 0:
                return f"This list {wrong_id} of ID dose not exist in database. But Specified commands Successfully added for other ID"
            else:
                return f"This list {wrong_id} of ID dose not exist in database."
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return str(ex)


class DeleteBulkPermissionForUserApiView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request):
        try:
            data = request.data
            emails = data.get('emails', None)
            commands = data.get('commands', None)
            result = delete_bulk_permission_for_user(emails, commands)
            return JsonResponse({'result': result, 'status': 200})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


def set_permission_for_user(email):
    try:
        user_id = User.objects.get(email=email).id
        permission_profile_id = 21
        user_instance = UserPermissionProfile.objects.create(action='allow', is_active='t',
                                                             permission_profile_id=permission_profile_id,
                                                             user_id=user_id)
        user_profile_id = UserPermissionProfile.objects.get(user_id=user_id).id
        user_permission_profile_object = UserPermissionProfileObject.objects.filter(
            user_permission_profile_id=93).values_list('object_id',
                                                       flat=True)
        for item in user_permission_profile_object:
            instance = UserPermissionProfileObject.objects.create(object_id=item, content_type_id=16,
                                                                  user_permission_profile_id=user_profile_id)
        return instance
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return str(ex)


def set_bulk_permission_for_user(emails, commands):
    try:
        users_id = []
        commands_id = []
        users_profile_id = []
        for item in emails:
            users_id.append(User.objects.get(email=item).id)
        for item in users_id:
            users_profile_id.append(UserPermissionProfile.objects.get(user_id=item).id)
        for item in commands:
            commands_id.append(Command.objects.get(text=item).id)

        for item in users_profile_id:
            for command in commands_id:
                try:
                    UserPermissionProfileObject.objects.create(object_id=command, content_type_id=16,
                                                               user_permission_profile_id=item)
                except Exception as ex:
                    if "duplicate key value violates unique" in str(ex):
                        continue
                    else:
                        return str(ex)
        return "Specified commands successfully added for users."

    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return str(ex)


def delete_bulk_permission_for_user(emails, commands):
    try:
        users_id = []
        commands_id = []
        users_profile_id = []
        for item in emails:
            users_id.append(User.objects.get(email=item).id)
        for item in users_id:
            users_profile_id.append(UserPermissionProfile.objects.get(user_id=item).id)
        for item in commands:
            commands_id.append(Command.objects.get(text=item).id)

        for item in users_profile_id:
            for command in commands_id:
                try:
                    UserPermissionProfileObject.objects.get(object_id=command, content_type_id=16,
                                                            user_permission_profile_id=item).delete()

                except Exception as ex:
                    if "does not exist." in str(ex):
                        continue
                    else:
                        return str(ex)
        return "Specified commands successfully deleted for users."

    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return str(ex)


def update_permission_for_user(email):
    try:
        permission_profile_id = 21
        user_instance = UserPermissionProfile.objects.filter(permission_profile_id=permission_profile_id).values_list(
            'id',
            flat=True)
        for item in user_instance:
            instance = UserPermissionProfileObject.objects.create(object_id=100, content_type_id=16,
                                                                  user_permission_profile_id=item)
        print(user_instance)
        return ''
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return str(ex)


def set_dslam_permission_for_user(username):
    try:
        user_id = User.objects.get(username=username).id
        permission_profile_id = 21
        user_instance = UserPermissionProfile.objects.create(action='allow', is_active='t',
                                                             permission_profile_id=permission_profile_id,
                                                             user_id=user_id)
        user_profile_id = UserPermissionProfile.objects.get(user_id=user_id).id
        user_permission_profile_object = UserPermissionProfileObject.objects.filter(
            user_permission_profile_id=93).values_list('object_id',
                                                       flat=True)
        for item in user_permission_profile_object:
            instance = UserPermissionProfileObject.objects.create(object_id=item, content_type_id=16,
                                                                  user_permission_profile_id=user_profile_id)
        return instance
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return str(ex)


class PortmanCommandsLoggingViewSet(mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):

    serializer_class = PortmanLogSerializer
    permission_classes = (IsAuthenticated,)
    queryset = PortmanLog.objects.all()
    # pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = self.queryset
        username = self.request.query_params.get('username', None)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size
        if username:
            queryset = PortmanLog.objects.filter(username=username).order_by('-log_date') | PortmanLog.objects.filter(username='0'+username).order_by('-log_date')
        return queryset


class GetCommandHistoryResultAPIView(views.APIView):

    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request, format=None):
        try:
            command_id = request.data.get('id')
            print(command_id)
            result = PortmanLog.objects.get(id=command_id).response
            print(">>>>>>>>>>>>>>>>>>GetCommandHistoryResultAPIView")
            print(result)
            print(">>>>>>>>>>>>>>>>>>GetCommandHistoryResultAPIView")
            result = result.replace("Press any key to continue, 'n' to nopause,'e' to exit", "").replace("'", '"')
            result = json.loads(result)
            return JsonResponse({'result': result.get('result'), 'status': 200})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return Response({'message': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactGroupViewSet(viewsets.GenericViewSet,
                          mixins.ListModelMixin,):
    queryset = ContactGroup.objects.all()
    serializer_class = ContactGroupSerializer
    permission_classes = (IsAuthenticated, ContactGroupPermission)

    def get_queryset(self):
        queryset = self.queryset.filter(Q(creator__isnull=True) | Q(creator=self.request.user))

        return queryset.order_by('id')


class NotifiableUsersViewSet(viewsets.GenericViewSet,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin):
    queryset = ContactGroupIndex.objects.all()
    serializer_class = ContactGroupIndexSerializer
    permission_classes = (IsAuthenticated, NotificationManagement)

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id', None)
        group_id = self.request.query_params.get('group_id', None)
        group_name = self.request.query_params.get('group_name', None)
        city_id = self.request.query_params.get('city_id', None)
        entity_id = self.request.query_params.get('entity_id', None)
        queryset = self.queryset

        if city_id:
            queryset = queryset.filter(city__id=city_id)

        if group_id:
            queryset = queryset.filter(group__id=group_id)
        if group_name:
            queryset = queryset.filter(group__name__icontains=group_name)

        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)

        if user_id:
            queryset = queryset.filter(user__id=user_id)

        return queryset.distinct('user__id')

    def create(self, request, *args, **kwargs):
        add_user_list = request.data.get('add_users', None)
        delete_user_list = request.data.get('delete_users', None)
        group_name = request.data.get('group_name', None)
        group_id = request.data.get('group_id', None)
        city_id = request.data.get('city_id', None)
        entity_id = request.data.get('entity_id', None)
        group_id = ContactGroup.objects.get(id=group_id).id
        for user_id in add_user_list:
            item = dict(user=user_id, group=group_id, city=city_id, entity_id=entity_id)
            serializer = self.serializer_class(data=item)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        for obj_id in delete_user_list:
            instance = ContactGroupIndex.objects.get(id=obj_id)
            self.perform_destroy(instance)

        return Response(dict(results='Success'), status=status.HTTP_200_OK)


class SendMessageApiView(views.APIView):
    def get_permissions(self):
        return (permissions.IsAuthenticated(), NotificationManagement())

    def post(self, request):
        try:
            data = request.data
            sender_id = request.user.id
            receiver_ids = data.get('user_id', None)
            message = data.get('message', None)
            send_type = data.get('send_type', None)
            sender_obj = User.objects.get(id=sender_id)
            receiver_objs = User.objects.filter(id__in=receiver_ids)
            status_send_message = False
            if 'in_app' in send_type:
                for receiver in receiver_objs:
                    status_send_message = save_notif_log(sender_obj, receiver, message, 'in_app')
            if 'sms' in send_type:
                status_send_message = send_message(sender_obj, receiver_objs, message, 'sms')
            if status_send_message:
                return JsonResponse(dict(results='Successfully sent.'), status=status.HTTP_200_OK)
            else:
                return JsonResponse(dict(results="Couldn't send message!"), status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})


class ShowNotificationLogViewSet(viewsets.GenericViewSet,
                                 mixins.ListModelMixin):
    serializer_class = ShowNotificationLogSerializer
    queryset = NotificationLog.objects.all()
    permission_classes = (IsAuthenticated, NotificationManagement)

    def get_queryset(self):
        queryset = self.queryset
        page_size = self.request.query_params.get('page_size', 10)
        sender_id = self.request.query_params.get('sender_id', None)
        receiver_id = self.request.query_params.get('receiver_id', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if sender_id:
            queryset = queryset.filter(sender__id=sender_id)
        if receiver_id:
            queryset = queryset.filter(receiver__id=receiver_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date+' 23:59:59')
        pagination.PageNumberPagination.page_size = page_size
        return queryset.order_by('-id')


class ProvinceAccessViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, AccessManagement)
    serializer_class = ProvinceAccessSerializer

    def get_queryset(self):
        queryset = ProvinceAccess.objects.all().order_by('-id')
        user_id = self.request.query_params.get('user_id', None)
        province_id = self.request.query_params.get('province_id', None)
        username = self.request.query_params.get('username', None)
        province_name = self.request.query_params.get('province_name', None)

        if user_id:
            queryset = queryset.filter(user__id=user_id)

        if province_id:
            queryset = queryset.filter(province__id=province_id)

        if username:
            queryset = queryset.filter(user__username__icontains=username)

        if province_name:
            queryset = queryset.filter(province__name__icontains=province_name)

        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset


class InstallersViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = InstallerSerializer

    def get_queryset(self):
        queryset = User.objects.filter(groups__name__in=[FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT]).distinct().order_by('-id')
        province_id = self.request.query_params.get('province_id', None)
        first_name = self.request.query_params.get('first_name', None)
        last_name = self.request.query_params.get('last_name', None)
        page_size = self.request.query_params.get('page_size')
        self.pagination_class.page_size = page_size if page_size else len(queryset)


        if province_id:
            users_id = ProvinceAccess.objects.filter(province_id=province_id,
                                                     province__parent__isnull=True).values_list('user_id', flat=True)
            queryset = queryset.filter(id__in=users_id)

        if first_name:
            searchForFirstName = Q(first_name__icontains=first_name)
            searchForFaFirstName = Q(fa_first_name__icontains=first_name)
            queryset = queryset.filter(searchForFirstName | searchForFaFirstName)

        if last_name:
            searchForLastName = Q(last_name__icontains=last_name)
            searchForFaLastName = Q(fa_last_name__icontains=last_name)
            queryset = queryset.filter(searchForLastName | searchForFaLastName)

        return queryset

    def create(self, request, *args, **kwargs):
        if not request.data.get('type', None):
            raise ValidationError(dict(results='Please enter type. It can be ftth_installer or ftth_cabler.'))
        request.data['user_type'] = request.data['type']
        request.data.pop('type', None)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        if not request.data.get('type', None):
            raise ValidationError(dict(results='Please enter type. It can be ftth_installer or ftth_cabler.'))
        request.data['user_type'] = request.data['type']
        request.data.pop('type', None)
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if FTTH_INSTALLER in instance.type or FTTH_CABLER in instance.type or FTTH_TECH_AGENT in instance.type:
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update_user_groups_and_type(self, obj, user_type):
        user_types = [ut.strip() for ut in user_type.split(",") if ut.strip()]

        selected_groups = []
        user_type_list = []

        if 'ftth_installer' in user_types:
            user_type_list.append(FTTH_INSTALLER)
            selected_groups.extend(AuthGroup.objects.filter(name=FTTH_INSTALLER).values_list('id', flat=True))

        if 'ftth_cabler' in user_types:
            user_type_list.append(FTTH_CABLER)
            selected_groups.extend(AuthGroup.objects.filter(name=FTTH_CABLER).values_list('id', flat=True))

        if 'ftth_tech_agent' in user_types:
            user_type_list.append(FTTH_TECH_AGENT)
            selected_groups.extend(AuthGroup.objects.filter(name=FTTH_TECH_AGENT).values_list('id', flat=True))

        obj.groups.set(selected_groups)
        obj.type = ",".join(user_type_list)
        obj.save()

    def perform_create(self, serializer):
        obj = serializer.save()
        user_type = self.request.data.get('user_type', '')
        self.update_user_groups_and_type(obj, user_type)

    def perform_update(self, serializer):
        serializer.save()
        instance = self.get_object()
        user_type = self.request.data.get('user_type', '')
        self.update_user_groups_and_type(instance, user_type)


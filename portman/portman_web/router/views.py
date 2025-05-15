import datetime
import sys, os
from datetime import time
import json
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from requests import Response
from rest_framework import status, views, mixins, viewsets, permissions
from router import utility
from router.models import Router, RouterCommand, NgnDevice
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import IsAuthenticated
from router.serializers import RouterSerializer, NgnDeviceSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from router.serializers import RouterSerializer, RouterCommandSerializer
from classes.base_permissions import ADMIN, SUPPORT, DIRECTRESELLER, RESELLER
from django.db import connection
from classes.base_permissions import NGN_ADMIN, INFRA_ADMIN
from config.settings import MIKROTIK_ROUTER_BACKUP_PATH, CISCO_ROUTER_BACKUP_PATH, VOIP_BACKUP_PATH
from django.db.models import Q


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = max


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = max

"""
class RouterRunCommandAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request):
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            user = request.user
            data = request.data
            return JsonResponse({'Result': request.data.get('fqdn')}, status=status.HTTP_200_OK)
            s = []
            command = data.get('command', None)
            params = data.get('params', None)
            subscriber = data.get('subscriber')
            fqdn = request.data.get('fqdn')
            routerObj = Router.objects.get(fqdn=fqdn)
            result = utility.router_run_command(routerObj.pk, command, params)
            return JsonResponse({'response': result})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse(
                {'result': str('an error occurred. please try again. {0}'.format(str(exc_tb.tb_lineno)))},
                status=status.HTTP_202_ACCEPTED)
"""


class RouterViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    queryset = Router.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RouterSerializer
    #pagination_class = LargeResultsSetPagination

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_superuser:
            print((self.request.user.type))
            return RouterSerializer(request=self.request, *args, **kwargs)
        elif self.request.user.type_contains(SUPPORT):
            print((self.request.user.type))
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return RouterSerializer(request=self.request, *args, **kwargs)
        else:
            print((self.request.user.type))
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return RouterSerializer(request=self.request, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def current(self, request):
        serializer = RouterSerializer(request.user, request=request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        sort_field = self.request.query_params.get('sort_field', None)
        router_name = self.request.query_params.get('search_router', None)
        device_ip = self.request.query_params.get('search_ip', None)
        ip_list = self.request.query_params.get('search_ip_list', None)
        city_id = self.request.query_params.get('search_city', None)
        telecom = self.request.query_params.get('search_telecom', None)
        device_fqdn = self.request.query_params.get('search_fqdn', None)
        active = self.request.query_params.get('search_active', None)
        status = self.request.query_params.get('search_status', None)
        router_type_id = self.request.query_params.get('search_type', None)
        page_size = self.request.query_params.get('page_size', 10)
        PageNumberPagination.page_size = page_size

        infraFilter = Q(host__host_group__group_name__icontains='Infrastructure')
        tehDcFilter = Q(host__host_group__group_name__icontains='-Teh-DC-')
        if user.type_contains([INFRA_ADMIN]):
            queryset = queryset.filter(infraFilter | tehDcFilter) 
        elif not user.type_contains([ADMIN]):
            queryset = queryset.exclude(infraFilter | tehDcFilter) 


        if router_type_id:
            queryset = queryset.filter(router_type__id=router_type_id)

        if router_name:
            queryset = queryset.filter(device_name__istartswith=router_name)

        if device_ip:
            device_ip = device_ip.strip()
            if len(device_ip.split('.')) != 4:
                queryset = queryset.filter(device_ip__istartswith=device_ip)
            else:
                queryset = queryset.filter(device_ip=device_ip)
        if device_fqdn:
            queryset = queryset.filter(device_fqdn__icontains=device_fqdn)
        if ip_list:
            for ip in ip_list.split(','):
                queryset = queryset.filter(device_ip__istartswith=ip)

        if status:
            queryset = queryset.filter(status=status)

        if active:
            queryset = queryset.filter(active=bool(active))

        if city_id:
            city = City.objects.get(id=city_id)
            if city.parent is None:
                city_ids = City.objects.filter(parent=city).values_list('id', flat=True)
                telecom_ids = TelecomCenter.objects.filter(city__id__in=city_ids).values_list('id', flat=True)
            else:
                telecom_ids = TelecomCenter.objects.filter(city=city).values_list('id', flat=True)
            queryset = queryset.filter(telecom_center__id__in=telecom_ids)

        if telecom:
            telecom_obj = TelecomCenter.objects.get(id=telecom)
            queryset = queryset.filter(telecom_center=telecom_obj)

        if sort_field:
            if sort_field.replace('-', '') in ('telecom_center',):
                sort_field += '__name'
            elif sort_field.replace('-', '') in ('city',):
                sort_field = sort_field.replace('city', 'telecom_center__city__name')

            queryset = queryset.order_by(sort_field)

        return queryset


class RouterRunCommandAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            data = request.data
            router_id = data.get('router_id')
            params = data.get('params')
            command = data.get('command')
            result = utility.router_run_command(router_id, command, params)
            if command == 'get Backup':
                return JsonResponse({'response': result})
            return JsonResponse({'response': result})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'Error': str(ex), 'Line': str(exc_tb.tb_lineno)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RouterCommandViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = RouterCommandSerializer
    permission_classes = (IsAuthenticated,)
    queryset = RouterCommand.objects.all()
    paginate_by = None
    paginate_by_param = None
    paginator = None

    def get_queryset(self):
        user = self.request.user
        RouterCommands = self.queryset

        limit_row = self.request.query_params.get('limit_row', None)
        router_type_id = self.request.query_params.get('router_type_id', None)
        router_command_description = self.request.query_params.get('command_type', None)
        router_command_text = self.request.query_params.get('command_type', None)
        try:
            if router_type_id:
                RouterCommands = RouterCommands.filter(router_type_id=router_type_id)
            if limit_row:
                RouterCommands = RouterCommands.filter(router_type_id=router_type_id)[:int(limit_row)]
            else:
                RouterCommands = RouterCommands.filter(router_type_id=router_type_id)
            return RouterCommands
        except:
            return []


class GetRouterBackupFilesNameAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            router_id = request.data.get('router_id')
            router_obj = Router.objects.get(id=router_id)
            fqdn = router_obj.device_fqdn
            ip = router_obj.device_ip
            filenames = []
            directory = MIKROTIK_ROUTER_BACKUP_PATH
            for filename in os.listdir(directory):
                # if (filename.__contains__(fqdn) or filename.__contains__(ip)) and filename.__contains__(str(datetime.datetime.now().date() - datetime.timedelta(1))):
                if filename.__contains__(fqdn) or filename.__contains__(ip):
                    filenames.append(filename)
                else:
                    continue
            return JsonResponse({'response': filenames})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class File:
    file_name = ''
    file_date = ''


class GetRouterBackupFilesNameAPIView2(views.APIView):
    def post(self, request, format=None):
        try:
            date_array = []
            for i in range(0, 14):
                date_array.append(str(datetime.datetime.now().date() - datetime.timedelta(i)))
            router_id = request.data.get('router_id')
            router_obj = Router.objects.get(id=router_id)
            router_type_id = router_obj.router_brand_id
            if router_type_id == 1:
                router_path = CISCO_ROUTER_BACKUP_PATH
            elif router_type_id == 2:
                router_path = MIKROTIK_ROUTER_BACKUP_PATH
            else:
                return None
            fqdn = router_obj.device_fqdn
            if fqdn:
                fqdn = fqdn.lower()
            ip = router_obj.device_ip
            filenames = []
            filenames_error = []
            directory = router_path
            for filename in os.listdir(directory):
                fileobj = File()
                temp_filename = filename.lower()
                # if (filename.__contains__(fqdn) or filename.__contains__(ip)) and filename.__contains__(str(datetime.datetime.now().date() - datetime.timedelta(1))):
                if 'error' in temp_filename:
                    if (temp_filename.__contains__(fqdn) or temp_filename.__contains__(ip)) and temp_filename.__contains__('@'):
                        for item in date_array:
                            if item in filename:
                                fileobj.file_name = filename
                                fileobj.file_date = filename.split('_')[2].split('.')[0]
                                filenames_error.append(fileobj)
                else:
                    if temp_filename.__contains__(fqdn) and temp_filename.__contains__('@'):
                        for item in date_array:
                            if item in filename:
                                fileobj.file_name = filename
                                fileobj.file_date = filename.split('_')[1].split('.')[0]
                                filenames.append(fileobj)
            total = filenames + filenames_error
            return JsonResponse({'response': json.dumps(total, default=lambda o: o.__dict__,
                                                        sort_keys=True, indent=4)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class DownloadRouterBackupFileAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            download_backup_file = request.data.get('backup_file_name')
            router_id = request.data.get('router_id')
            router_obj = Router.objects.get(id=router_id)
            router_ip = router_obj.device_ip
            host_groups = ['Infrastructure', 'Voip-NGN', '-Teh-DC-']
            if self.is_permission_required(host_groups, router_ip):
                user_ldap_groups = self.request.user.ldap_group_name
                if user_ldap_groups:
                    if 'Datacenter' not in user_ldap_groups or not request.user.type_contains([INFRA_ADMIN]):
                        return JsonResponse({"results": "You don't have permission to download the file."}, status=status.HTTP_403_FORBIDDEN)
                else:
                    if not self.request.user.type_contains('ADMIN'):
                        return JsonResponse({"results": "You don't have permission to download the file."},
                                            status=status.HTTP_403_FORBIDDEN)

            router_type_id = router_obj.router_brand_id
            if router_type_id == 1:
                router_path = CISCO_ROUTER_BACKUP_PATH
            elif router_type_id == 2:
                router_path = MIKROTIK_ROUTER_BACKUP_PATH
            else:
                return None
            directory = router_path + download_backup_file
            f = open(directory, "r")
            return JsonResponse({'response': f.read()})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

    def is_permission_required(self, host_groups, device_ip):
        cursor = connection.cursor()
        for host_group in host_groups:
            query = f"SELECT DISTINCT z.device_ip FROM zabbix_hosts AS z JOIN zabbix_hostgroups AS h ON z.host_group_id = h.id WHERE h.group_name LIKE '%{host_group}%' AND z.device_ip = '{device_ip}';"
            cursor.execute(query)
            if cursor.fetchall():
                return True
        return False


class GetRouterBackupErrorFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            filenames = []
            directory = MIKROTIK_ROUTER_BACKUP_PATH
            for filename in os.listdir(directory):
                if filename.__contains__('Error'):
                    filenames.append(filename)
                else:
                    continue
            return JsonResponse({'response': filenames})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class ReadRouterBackupErrorFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            if os.path.exists(MIKROTIK_ROUTER_BACKUP_PATH + 'router_backup_errors.txt'):
                os.remove(MIKROTIK_ROUTER_BACKUP_PATH + 'router_backup_errors.txt')
            filenames = []
            directory = MIKROTIK_ROUTER_BACKUP_PATH
            backup_errors_file = open(MIKROTIK_ROUTER_BACKUP_PATH + 'router_backup_errors.txt', 'w')
            for filename in os.listdir(directory):
                if filename.__contains__('Error') and filename.__contains__(
                        str(datetime.datetime.now().date() - datetime.timedelta(1))):
                    f = open(directory + filename, "r")
                    err_text = filename + "   " + "|" + "   " + f.read()
                    backup_errors_file.write(filename + '     ' + f.read() + '\n')
                    filenames.append(err_text)
                    f.close()
                else:
                    continue
            backup_errors_file.close()
            return JsonResponse({'response': filenames})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class SetSSLOnRouter(views.APIView):

    def post(self, request, format=None):
        try:
            data = request.data
            router_id = data['router_id']
            params = data.get('params')
            command = data.get('command')
            result = utility.router_run_command(router_id, command, params)
            return JsonResponse({'response': result})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetRouterBackupFileNameWithDate(views.APIView):
    def post(self, request):
        try:
            data = request.data
            router_id = data.get('router_id')
            date = data.get('date')
            router_obj = Router.objects.get(id=router_id)
            router_type_id = router_obj.router_brand_id
            fqdn = router_obj.device_fqdn
            total = []
            filenames = []
            filenames_error = []
            if router_type_id == 1:
                router_path = CISCO_ROUTER_BACKUP_PATH
            elif router_type_id == 2:
                router_path = MIKROTIK_ROUTER_BACKUP_PATH
            else:
                return None
            directory = router_path
            for filename in os.listdir(directory):
                fileobj = File()
                if 'Error' in filename:
                    if filename.__contains__(fqdn) and filename.__contains__(date):
                            fileobj.file_name = filename
                            fileobj.file_date = filename.split('_')[2].split('.')[0]
                            filenames_error.append(fileobj)
                else:
                    if filename.__contains__(fqdn) and filename.__contains__(date):
                            fileobj.file_name = filename
                            fileobj.file_date = filename.split('_')[1].split('.')[0]
                            filenames.append(fileobj)
            total.append(filenames_error)
            total.append(filenames)
            if len(total) != 0:
                return JsonResponse({'response': json.dumps(total, default=lambda o: o.__dict__,
                                                            sort_keys=True, indent=4)})
            else:
                return JsonResponse({'response': 'There are no backups on this date!'})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class NgnDeviceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = NgnDevice.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = NgnDeviceSerializer
    #pagination_class = StandardResultsSetPagination

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_superuser:
            print((self.request.user.type))
            return NgnDeviceSerializer(request=self.request, *args, **kwargs)
        elif self.request.user.type_contains(SUPPORT):
            print((self.request.user.type))
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return NgnDeviceSerializer(request=self.request, *args, **kwargs)
        else:
            print((self.request.user.type))
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return NgnDeviceSerializer(request=self.request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if not user.type_contains([NGN_ADMIN, ADMIN]):
            return queryset.filter(id=0) # return empty list

        sort_field = self.request.query_params.get('sort_field', None)
        router_name = self.request.query_params.get('search_router', None)
        device_ip = self.request.query_params.get('search_ip', None)
        ip_list = self.request.query_params.get('search_ip_list', None)
        city_id = self.request.query_params.get('search_city', None)
        telecom = self.request.query_params.get('search_telecom', None)
        device_fqdn = self.request.query_params.get('search_fqdn', None)
        active = self.request.query_params.get('search_active', None)
        status = self.request.query_params.get('search_status', None)
        router_type_id = self.request.query_params.get('search_type', None)
        page_size = self.request.query_params.get('page_size', 10)
        PageNumberPagination.page_size = page_size

        if router_type_id:
            queryset = queryset.filter(router_type__id=router_type_id)

        if router_name:
            queryset = queryset.filter(device_name__istartswith=router_name)

        if device_ip:
            device_ip = device_ip.strip()
            if len(device_ip.split('.')) != 4:
                queryset = queryset.filter(device_ip__istartswith=device_ip)
            else:
                queryset = queryset.filter(device_ip=device_ip)
        if device_fqdn:
            queryset = queryset.filter(device_fqdn__icontains=device_fqdn)
        if ip_list:
            for ip in ip_list.split(','):
                queryset = queryset.filter(device_ip__istartswith=ip)

        if status:
            queryset = queryset.filter(status=status)

        if active:
            queryset = queryset.filter(active=bool(active))

        if city_id:
            city = City.objects.get(id=city_id)
            if city.parent is None:
                city_ids = City.objects.filter(parent=city).values_list('id', flat=True)
                telecom_ids = TelecomCenter.objects.filter(city__id__in=city_ids).values_list('id', flat=True)
            else:
                telecom_ids = TelecomCenter.objects.filter(city=city).values_list('id', flat=True)
            queryset = queryset.filter(telecom_center__id__in=telecom_ids)

        if telecom:
            telecom_obj = TelecomCenter.objects.get(id=telecom)
            queryset = queryset.filter(telecom_center=telecom_obj)

        if sort_field:
            if sort_field.replace('-', '') in ('telecom_center',):
                sort_field += '__name'
            elif sort_field.replace('-', '') in ('city',):
                sort_field = sort_field.replace('city', 'telecom_center__city__name')

            queryset = queryset.order_by(sort_field)

        return queryset


class GetNgnDeviceBackupFilesNameAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            date_array = []
            for i in range(0, 7):
                date_array.append(str(datetime.datetime.now().date() - datetime.timedelta(i)))
            ngn_device_id = request.data.get('device_id')
            ngn_device_obj = NgnDevice.objects.get(pk=ngn_device_id)
            router_type_id = ngn_device_obj.router_brand_id
            if router_type_id == 1:
                router_path = VOIP_BACKUP_PATH
            elif router_type_id == 2:
                router_path = VOIP_BACKUP_PATH
            else:
                return None
            fqdn = ngn_device_obj.device_fqdn
            ip = ngn_device_obj.device_ip
            filenames = []
            filenames_error = []
            directory = router_path
            for filename in os.listdir(directory):
                fileobj = File()
                # if (filename.__contains__(fqdn) or filename.__contains__(ip)) and filename.__contains__(str(datetime.datetime.now().date() - datetime.timedelta(1))):
                if 'Error' in filename:
                    if filename.__contains__(fqdn) and filename.__contains__('@'):
                        for item in date_array:
                            if item in filename:
                                fileobj.file_name = filename
                                fileobj.file_date = filename.split('_')[2].split('.')[0]
                                filenames_error.append(fileobj)
                else:
                    if filename.__contains__(fqdn) and filename.__contains__('@'):
                        for item in date_array:
                            if item in filename:
                                fileobj.file_name = filename
                                fileobj.file_date = filename.split('_')[1].split('.')[0]
                                filenames.append(fileobj)

            total = filenames + filenames_error
            return JsonResponse({'response': json.dumps(total, default=lambda o: o.__dict__,
                                                        sort_keys=True, indent=4)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

class DownloadNgnDeviceBackupFileAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            # '172.28.65.28' '109.110.160.155

            download_backup_file = request.data.get('backup_file_name')
            device_id = request.data.get('device_id')
            ngn_device_obj = NgnDevice.objects.get(pk=device_id)

            host_groups = ['Infrastructure', 'Voip-NGN', '-Teh-DC-']
            if self.is_permission_required(host_groups, ngn_device_obj.device_ip):
                user_ldap_groups = self.request.user.ldap_group_name
                if user_ldap_groups:
                    if 'Datacenter' not in user_ldap_groups or not request.user.type_contains([NGN_ADMIN]):
                        return JsonResponse({"results": "You don't have permission to download the file."}, status=status.HTTP_403_FORBIDDEN)
                else:
                    if not self.request.user.type_contains('ADMIN'):
                        return JsonResponse({"results": "You don't have permission to download the file."},
                                            status=status.HTTP_403_FORBIDDEN)

            router_type_id = ngn_device_obj.router_brand_id
            if router_type_id == 1:
                router_path = VOIP_BACKUP_PATH
            elif router_type_id == 2:
                router_path = VOIP_BACKUP_PATH
            else:
                return None
            directory = router_path + download_backup_file
            f = open(directory, "r")
            return JsonResponse({'response': f.read()})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

    def is_permission_required(self, host_groups, device_ip):
        cursor = connection.cursor()
        for host_group in host_groups:
            query = f"SELECT DISTINCT z.device_ip FROM zabbix_hosts AS z JOIN zabbix_hostgroups AS h ON z.host_group_id = h.id WHERE h.group_name LIKE '%{host_group}%' AND z.device_ip = '{device_ip}';"
            cursor.execute(query)
            if cursor.fetchall():
                return True
        return False

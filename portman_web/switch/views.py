import datetime
import json
import sys, os
from pathlib import Path
from wsgiref.util import FileWrapper
from datetime import time
from rest_framework import status, views, mixins, viewsets, permissions
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import IsAuthenticated
from switch.serializers import SwitchSerializer, SwitchCommandSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from switch.models import Switch, SwitchCommand
from switch import utility
from config import settings
import concurrent.futures
from glob import glob
from django.db import connection
from classes.base_permissions import NGN_ADMIN, INFRA_ADMIN, SUPPORT, ADMIN
from config.settings import SWITCH_BACKUP_PATH
from config.settings import VLAN_BRIEF_PATH

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = max


class SwitchViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    #queryset = Switch.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = SwitchSerializer
    #pagination_class = LargeResultsSetPagination

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_superuser:
            print(self.request.user.type)
            return SwitchSerializer(request=self.request, *args, **kwargs)
        elif self.request.user.type_contains(SUPPORT):
            print(self.request.user.type)
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return SwitchSerializer(request=self.request, *args, **kwargs)
        else:
            print(self.request.user.type)
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''

            return SwitchSerializer(request=self.request, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def current(self, request):
        serializer = SwitchSerializer(request.user, request=request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = Switch.objects.all() #self.queryset
        user = self.request.user

        sort_field = self.request.query_params.get('sort_field', None)
        switch_name = self.request.query_params.get('search_switch', None)
        device_ip = self.request.query_params.get('search_ip', None)
        ip_list = self.request.query_params.get('search_ip_list', None)
        city_id = self.request.query_params.get('search_city', None)
        telecom = self.request.query_params.get('search_telecom', None)
        active = self.request.query_params.get('search_active', None)
        status = self.request.query_params.get('search_status', None)
        switch_type_id = self.request.query_params.get('search_type', None)
        device_fqdn = self.request.query_params.get('search_fqdn', None)
        page_size = self.request.query_params.get('page_size', 10)
        PageNumberPagination.page_size = page_size

        if user.type_contains([INFRA_ADMIN]):
            queryset = queryset.filter(host__host_group__group_name__icontains='Infrastructure') 
        elif not user.type_contains([ADMIN]):
            queryset = queryset.exclude(host__host_group__group_name__icontains='Infrastructure') 

        if switch_type_id:
            queryset = queryset.filter(switch_type__id=switch_type_id)

        if switch_name:
            queryset = queryset.filter(device_name__istartswith=switch_name)

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
                queryset = queryset.filter(ip__istartswith=ip)

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


class SwitchRunCommandAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            data = request.data
            switch_id = data.get('switch_id')
            params = data.get('params')
            command = data.get('command')
            result = utility.switch_run_command(switch_id, command, params)
            if command == 'show dot1x':
                return JsonResponse({'response': result})
            if command == 'show ip dhcp snooping':
                return JsonResponse({'response': result})
            return JsonResponse({'response': result})


        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex)})


class SwitchCommandViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = SwitchCommandSerializer
    permission_classes = (IsAuthenticated,)
    queryset = SwitchCommand.objects.all()
    paginate_by = None
    paginate_by_param = None
    paginator = None

    def get_queryset(self):
        user = self.request.user
        SwitchCommands = self.queryset

        limit_row = self.request.query_params.get('limit_row', None)
        switch_type_id = self.request.query_params.get('switch_type_id', None)
        switch_command_description = self.request.query_params.get('command_type', None)
        switch_command_text = self.request.query_params.get('command_type', None)
        try:
            if switch_type_id:
                SwitchCommands = SwitchCommands.filter(switch_type_id=switch_type_id)
            if limit_row:
                SwitchCommands = SwitchCommands.filter(switch_type_id=switch_type_id)[:int(limit_row)]
            else:
                SwitchCommands = SwitchCommands.filter(switch_type_id=switch_type_id)
            return SwitchCommands
        except:
            return []


class GetBackupFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            switch_id = request.data.get('switch_id')
            switch_obj = Switch.objects.get(id=switch_id)
            fqdn = switch_obj.device_fqdn
            ip = switch_obj.device_ip
            filenames = []
            directory = SWITCH_BACKUP_PATH
            for filename in os.listdir(directory):
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


class GetSwitchBackupFilesNameAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            switch_id = request.data.get('switch_id')
            switch_obj = Switch.objects.filter(id=switch_id).first()
            ip =  switch_obj.device_ip
            fqdn = switch_obj.device_fqdn
            date_array = {str(datetime.datetime.now().date() - datetime.timedelta(i)) for i in range(0, 7)}

            file_paths = glob(f"{SWITCH_BACKUP_PATH}/*{fqdn}*")
            if not file_paths:
                file_paths = glob(f"{SWITCH_BACKUP_PATH}/*{ip}*")
            total = []

            for file_path in file_paths:
                path_obj = Path(file_path)
                filename = path_obj.name
                if any(item in filename for item in date_array):
                    file_dict = {
                        'file_name': filename,
                        'file_date': filename.split('@')[1].split('_')[1].split('.')[0]
                    }
                    total.append(file_dict)

            return JsonResponse({'response': json.dumps(total, default=lambda o: o.__dict__,
                                                        sort_keys=True, indent=4)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class DownloadBackupFileAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            download_backup_file = request.data.get('backup_file_name')
            switch_ip = download_backup_file.split('@')[1].split('_')[0]
            host_groups = ['Infrastructure', 'Voip-NGN']
            if self.is_permission_required(host_groups, switch_ip):
                user_ldap_groups = self.request.user.ldap_group_name
                if user_ldap_groups:
                    if 'Datacenter' not in user_ldap_groups or not request.user.type_contains([INFRA_ADMIN]):
                        return JsonResponse({"results": "You don't have permission to download the file."},
                                            status=status.HTTP_403_FORBIDDEN)
                else:
                    if not self.request.user.type_contains('ADMIN'):
                        return JsonResponse({"results": "You don't have permission to download the file."},
                                            status=status.HTTP_403_FORBIDDEN)
            directory = SWITCH_BACKUP_PATH + download_backup_file
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


class GetBackupErrorFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            filenames = []
            directory = SWITCH_BACKUP_PATH
            for filename in os.listdir(directory):
                if filename.__contains__('Error'):
                    filenames.append(filename)
                else:
                    continue
            directory2 = "/opt/portmanv3/portman_core2/router_vendors/mikrotik_commands/Backups/"
            for filename2 in os.listdir(directory2):
                if filename2.__contains__('Error'):
                    filenames.append(filename2)
                else:
                    continue
            return JsonResponse({'response': filenames})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetBackupErrorTextNameAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            backup_file_name = request.data.get('backup_file_name')
            directory = SWITCH_BACKUP_PATH + backup_file_name
            f = open(directory, "r")
            return JsonResponse({'response': f.read()})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class ReadSwitchBackupErrorFilesNameAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            if os.path.exists(SWITCH_BACKUP_PATH + 'switch_backup_errors.txt'):
                os.remove(SWITCH_BACKUP_PATH + 'switch_backup_errors.txt')
            filenames = []
            directory = SWITCH_BACKUP_PATH
            backup_errors_file = open(SWITCH_BACKUP_PATH + 'switch_backup_errors.txt', 'w')
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


class GetSwitchShowVlanBriefFilesName(views.APIView):

    def post(self, request, format=None):
        try:
            switch_id = request.data.get('switch_id')
            switch_obj = Switch.objects.get(id=switch_id)
            fqdn = switch_obj.device_fqdn
            date_array = {str(datetime.datetime.now().date() - datetime.timedelta(i)) for i in range(0, 7)}

            file_paths = glob(f"{VLAN_BRIEF_PATH}/*{fqdn}*")
            total = []

            for file_path in file_paths:
                path_obj = Path(file_path)
                filename = path_obj.name
                if any(item in filename for item in date_array):
                    file_dict = {
                        'file_name': filename,
                        'file_date': filename.split('@')[1].split('_')[1].split('.')[0]
                    }
                    total.append(file_dict)


            return JsonResponse({'response': json.dumps(total, default=lambda o: o.__dict__,
                                                        sort_keys=True, indent=4)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class DownloadViewVlanBriefFile(views.APIView):

    def post(self, request, format=None):
        try:
            vlan_brief_file_name = request.data.get('vlan_brief_file_name')
            vlan_directory = VLAN_BRIEF_PATH + vlan_brief_file_name
            f = open(vlan_directory, "r")
            return JsonResponse({'response': f.read()})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

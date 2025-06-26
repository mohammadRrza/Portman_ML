import datetime
import sys, os
import json

from requests import Response
from rest_framework import status, views, mixins, viewsets, permissions
from radio import utility
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from radio.models import Radio, RadioCommand
from radio.serializers import RadioSerializer, RadioCommandSerializer
from django.core.serializers import serialize
from classes.base_permissions import SUPPORT
from config.settings import RADIO_BACKUP_PATH


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = max


class RadioRunCommandAPIView(views.APIView):
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


class RadioViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    queryset = Radio.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = RadioSerializer
    #pagination_class = LargeResultsSetPagination

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_superuser:
            print((self.request.user.type))
            return RadioSerializer(request=self.request, *args, **kwargs)
        elif self.request.user.type_contains(SUPPORT):
            print((self.request.user.type))
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return RadioSerializer(request=self.request, *args, **kwargs)
        else:
            print((self.request.user.type))
            '''_fields = ['id', 'device_name', 'device_ip', 'device_fqdn']'''
            return RadioSerializer(request=self.request, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def current(self, request):
        serializer = RadioSerializer(request.user, request=request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        sort_field = self.request.query_params.get('sort_field', None)
        router_name = self.request.query_params.get('search_radio', None)
        device_ip = self.request.query_params.get('search_ip', None)
        ip_list = self.request.query_params.get('search_ip_list', None)
        device_fqdn = self.request.query_params.get('search_fqdn', None)
        active = self.request.query_params.get('search_active', None)
        status = self.request.query_params.get('search_status', None)
        ratio_type_id = self.request.query_params.get('search_type', None)

        if ratio_type_id:
            queryset = queryset.filter(radio_type__id=ratio_type_id)

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


class RadioCommandViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    serializer_class = RadioCommandSerializer
    permission_classes = (IsAuthenticated,)
    queryset = RadioCommand.objects.all()
    paginate_by = None
    paginate_by_param = None
    paginator = None

    def get_queryset(self):
        queryset = RadioCommand.objects.all()
        limit_row = self.request.query_params.get('limit_row', None)
        radio_type_id = self.request.query_params.get('radio_type_id', None)
        router_command_description = self.request.query_params.get('command_type', None)
        router_command_text = self.request.query_params.get('command_type', None)
        try:
            if radio_type_id:
                print('radio_type_id:' + radio_type_id)
                queryset = queryset.filter(radio_type_id=radio_type_id)
            if limit_row:
                print('limit_row:' + limit_row)
                queryset = queryset.filter(radio_type_id=radio_type_id)[:int(limit_row)]
            else:
                queryset = queryset.filter(radio_type_id=radio_type_id)
            return queryset
        except Exception as ex:
            print(ex)
            return queryset


class File:
    file_name = ''
    file_date = ''


class GetRadioBackupFilesNameAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            date_array = []
            for i in range(0, 10):
                date_array.append(str(datetime.datetime.now().date() - datetime.timedelta(i)))

            radio_id = request.data['radio_id']
            radio_obj = Radio.objects.get(id=radio_id)
            fqdn = radio_obj.device_fqdn
            ip = radio_obj.device_ip
            filenames = []
            directory = RADIO_BACKUP_PATH
            for filename in os.listdir(directory):
                if filename.__contains__(fqdn) or filename.__contains__(ip):
                    for item in date_array:
                        if item in filename:
                            file_info = dict(file_name=filename, file_date=filename.split('@')[1].split('_')[1].split('.')[0])
                            filenames.append(file_info)
            return JsonResponse({'response': json.dumps(filenames, default=lambda o: o.__dict__,
                                                        sort_keys=True, indent=4)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class DownloadRadioBackupFileAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            download_backup_file = request.data.get('backup_file_name')
            directory = RADIO_BACKUP_PATH + download_backup_file
            f = open(directory, "r")
            return JsonResponse({'response': f.read()})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetRadioBackupErrorFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            filenames = []
            directory = RADIO_BACKUP_PATH
            for filename in os.listdir(directory):
                if filename.__contains__('Error'):
                    filenames.append(filename)
                else:
                    continue
            return JsonResponse({'response': filenames})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class ReadRadioBackupErrorFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            if os.path.exists(RADIO_BACKUP_PATH + 'radio_backup_errors.txt'):
                os.remove(RADIO_BACKUP_PATH + 'radio_backup_errors.txt')
            filenames = []
            directory = RADIO_BACKUP_PATH
            backup_errors_file = open(RADIO_BACKUP_PATH + 'radio_backup_errors.txt', 'w')
            for filename in os.listdir(RADIO_BACKUP_PATH):
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


class DownloadRadioBackupFileAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            download_backup_file = request.data.get('backup_file_name')
            directory = RADIO_BACKUP_PATH + download_backup_file
            f = open(directory, "r")
            return JsonResponse({'response': f.read()})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetRadioBackupErrorFilesNameAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            filenames = []
            directory = RADIO_BACKUP_PATH
            for filename in os.listdir(directory):
                if filename.__contains__('Error'):
                    filenames.append(filename)
                else:
                    continue
            return JsonResponse({'response': filenames})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class SetRadioGeographicalCoordinatesAPIView(views.APIView):

    def post(self, request, format=None):
        try:
            data = request.data
            radio_id = data['radio_id']
            params = data.get('params')
            command = data.get('command')
            result = utility.radio_run_command(radio_id, command, params)
            return JsonResponse({'response': result})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

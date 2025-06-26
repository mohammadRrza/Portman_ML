import json
import sys, os
import csv
from datetime import datetime
import requests
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import pagination
from rest_framework.exceptions import ValidationError
from django.views.generic import View
from django.db import connection
from rest_framework import status, views, mixins, viewsets, permissions
from contact.models import Order, Province, City, TelecommunicationCenters, PortmapState, FarzaneganTDLTE, \
    FarzaneganProviderData, DataLocationsLog, TechnicalProfile, TechnicalUser, PishgamanNoteLog
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import IsAuthenticated
from contact.serializers import OrderSerializer, DDRPageSerializer, FarzaneganSerializer, GetNotesSerializer, \
    GetDataLocationsLoggingSerializer, TechnicalUserSerializer, TechnicalProfileSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.core.serializers import serialize
from classes.mellat_bank_scrapping import get_captcha
from users.helpers import add_audit_log
# from classes.farzanegan_selenium import farzanegan_scrapping
# from portman_web.classes.farzanegan_selenium import farzanegan_scrapping
from contact.models import PishgamanNote
from .services.location_service import LocationServices
from .services.location_service_v2 import LocationServicesV2
from classes.base_permissions import SUPPORT
from classes.persian import unidecode
from .permissions import CanViewTechnicalProfileList
from django.views.decorators.cache import never_cache
from config.settings import MIKROTIK_ROUTER_BACKUP_PATH


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = max


class PortMapViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer
    #pagination_class = LargeResultsSetPagination

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_superuser:
            print(self.request.user.type)
            return OrderSerializer(request=self.request, *args, **kwargs)
        elif self.request.user.type_contains(SUPPORT):
            print(self.request.user.type)
            _fields = ['username', 'ranjePhoneNumber', 'slot_number', 'port_number', 'telecomCenter_info',
                       'telco_row', 'telco_column', 'telco_connection', 'fqdn', 'port_status_info']
            return OrderSerializer(request=self.request, remove_fields=_fields, *args, **kwargs)
        else:
            print(self.request.user.type)
            _fields = ['username', 'ranjePhoneNumber', 'slot_number', 'port_number', 'telecomCenter_info',
                       'telco_row', 'telco_column', 'telco_connection', 'fqdn', 'port_status_info']
            return OrderSerializer(request=self.request, remove_fields=_fields, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def current(self, request):
        serializer = OrderSerializer(request.user, request=request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        sort_field = self.request.query_params.get('sort_field', None)
        username = self.request.query_params.get('search_username', None)
        ranjePhoneNumber = self.request.query_params.get('search_ranjePhoneNumber', None)
        fqdn = self.request.query_params.get('search_ranjePhoneNumber', None)
        slot_number = self.request.query_params.get('search_slot_number', None)
        port_number = self.request.query_params.get('search_port_number', None)
        telco_row = self.request.query_params.get('search_telco_row', None)
        telco_Column = self.request.query_params.get('search_telco_Column', None)
        telco_connection = self.request.query_params.get('search_telco_connection', None)
        telecom_id = self.request.query_params.get('telecom_id')
        port_status_id = self.request.query_params.get('port_status_id')

        if username:
            queryset = queryset.filter(username__icontains=username)

        if ranjePhoneNumber:
            queryset = queryset.filter(ranjePhoneNumber__icontains=ranjePhoneNumber)

        if fqdn:
            queryset = queryset.filter(fqdn__icontains=fqdn)

        if slot_number:
            queryset = queryset.filter(slot_number=slot_number)

        if port_number:
            queryset = queryset.filter(port_number=port_number)

        if telco_row:
            queryset = queryset.filter(telco_row=telco_row)

        if telco_Column:
            queryset = queryset.filter(telco_Column=telco_Column)

        if telco_connection:
            queryset = queryset.filter(telco_connection=telco_connection)

        if telecom_id:
            queryset = queryset.filter(telecom_id=telecom_id)

        if port_status_id:
            queryset = queryset.filter(status_id=port_status_id)

        return queryset


class PortmapAPIView(views.APIView):

    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request, format=None):
        data = request.data
        queryset = Order.objects.all()

        username = data.get('username', None)
        province_name = data.get('province_name', None)
        city_name = data.get('city_name', None)
        telecom_name = data.get('telecom_name', None)
        status = data.get('status', None)
        port_owner = data.get('port_owner', None)
        port_type = data.get('port_type', None)
        search_type = data.get('search_type', None)
        from_row = data.get('from_row', 1)
        to_row = data.get('to_row', 1000)
        from_dslam = data.get('from_dslam', 1)
        to_dslam = data.get('to_dslam', 3)
        from_floor = data.get('from_floor', 1)
        to_floor = data.get('to_floor', 15)
        from_card = data.get('from_card', 1)
        to_card = data.get('to_card', 80)
        from_connection = data.get('from_connection', '1')
        to_connection = data.get('to_connection', '100')
        from_port = data.get('from_port', 1)
        to_port = data.get('to_port', 100)
        prefix_num = data.get('prefix_num', None)
        ranje_num = data.get('ranje_num', None)
        show_deleted = data.get('show_deleted', None)
        show_priorities = data.get('show_priorities', None)

        try:
            if province_name:
                queryset = queryset.filter(province_name__icontains=province_name)
            if city_name:
                queryset = queryset.filter(city_name__icontains=city_name)
            if telecom_name:
                queryset = queryset.filter(telecom_name__icontains=telecom_name)
            if status:
                queryset = queryset.filter(status=status)
            if port_owner:
                queryset = queryset.filter(port_owner__icontains=port_owner)
            if port_type:
                queryset = queryset.filter(port_type=port_type)
            if search_type == "bukht":
                queryset = queryset.filter(Q(telco_row__gte=from_row) & Q(telco_row__lte=to_row)).filter(
                    Q(telco_column__gte=from_row) & Q(telco_column__lte=to_row)).filter(
                    Q(telco_connection__gte=from_connection) & Q(telco_connection__lte=to_connection))
            if search_type == "port":
                queryset = queryset.filter(Q(from_row__gte=from_dslam) & Q(to_row__lte=to_dslam)).filter(
                    Q(from_row__gte=from_card) & Q(to_row__lte=to_card)).filter(
                    Q(from_row__gte=from_port) & Q(to_row__lte=to_port))
            if prefix_num:
                queryset = queryset.filter(prefix_num__icontains=prefix_num)
            if ranje_num:
                queryset = queryset.filter(ranje_num__icontains=ranje_num)
            if show_deleted:
                queryset = queryset.filter(show_deleted=show_deleted)
            if show_priorities:
                queryset = queryset.filter(show_priorities=show_priorities)
            result = serialize('json', queryset)
            return HttpResponse(result, content_type='application/json')

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetProvincesAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            province_name = request.query_params.get('province_name')
            if province_name:
                provinces = Province.objects.filter(provinceName__icontains=province_name).values().order_by(
                    'provinceName')[:10]
                return JsonResponse({"result": list(provinces)})
            provinces = Province.objects.all().values().order_by('provinceName')[:10]
            return JsonResponse({"result": list(provinces)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetCitiesByProvinceIdAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            province_id = request.query_params.get('province_id')
            city_name = request.query_params.get('city_name')

            if province_id and city_name:
                Cities = City.objects.filter(provinceId=province_id, cityName__icontains=city_name).values().order_by(
                    'cityName')[:10]
                return JsonResponse({"result": list(Cities)})
            Cities = City.objects.all().values().order_by('cityName')[:10]
            return JsonResponse({"result": list(Cities)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetTelecomsByCityIdAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            city_id = request.query_params.get('city_id')
            telecom_name = request.query_params.get('telecom_name')

            if city_id and telecom_name:
                telecoms = TelecommunicationCenters.objects.filter(city_id=city_id,
                                                                   name__icontains=telecom_name).values().order_by(
                    'name')[:10]
                return JsonResponse({"result": list(telecoms)})
            telecoms = TelecommunicationCenters.objects.all().values().order_by('name')[:10]
            return JsonResponse({"result": list(telecoms)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetPortsStatus(views.APIView):
    def get(self, request, format=None):
        try:
            statuses = PortmapState.objects.all().values().order_by('description')[:10]
            return JsonResponse({"result": list(statuses)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class SearchPorts(views.APIView):
    def get(self, request, format=None):
        try:
            province_id = request.query_params.get('province_id')
            city_id = request.query_params.get('city_id')
            telecom_id = request.query_params.get('telecom_id')
            port_status_id = request.query_params.get('port_status_id')
            """if province_id:
                query = 'select * from contact_order o INNER JOIN contact_telecommunicationcenters tc on tc."id" = o.telecom_id INNER JOIN contact_city ci on ci."id" = tc.city_id INNER JOIN contact_province cp on cp."id" = ci.province_id WHERE cp."id" = {0} limit 100'.format(province_id)
                cursor = connection.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                print(rows)
                return JsonResponse({"result": rows})
            if city_id:
                ports = Order.objects.select_related('telecom__city').filter(city_id=city_id)"""
            if telecom_id and port_status_id == "":
                ports = Order.objects.filter(telecom_id=telecom_id).values()
            if port_status_id and telecom_id:
                ports = Order.objects.filter(telecom_id=int(telecom_id), status_id=int(port_status_id)).values()
            return JsonResponse({"result": list(ports)})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class UpdateStatusPorts(views.APIView):
    def post(self, request, format=None):
        try:
            data = request.data
            username = data.get('username', None)
            new_port_status_id = data.get('port_status_id', None)
            order = Order.objects.get(username=username)
            order.status_id = new_port_status_id
            order.save()
            return JsonResponse(
                {"username": str(order.username), "status": str(order.status), "telecom": str(order.telecom)})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class UpdateStatusPorts2(views.APIView):
    def post(self, request, format=None):
        try:
            data = request.data
            username = data.get('username', None)
            ranjePhoneNumber = data.get('ranjePhoneNumber', None)
            old_port_status_id = data.get('old_port_status_id', None)
            new_port_status_id = data.get('new_port_status_id', None)
            telecom_id = data.get('telecom_id', None)
            telco_row = data.get('old_telco_row', None)
            telco_column = data.get('old_telco_column', None)
            telco_connection = data.get('old_telco_connection', None)
            new_telco_row = data.get('new_telco_row', None)
            new_telco_column = data.get('new_telco_column', None)
            new_telco_connection = data.get('new_telco_connection', None)
            try:
                old_order = Order.objects.get(telecom_id=telecom_id, telco_row=telco_row, telco_column=telco_column,
                                              telco_connection=telco_connection)
            except ObjectDoesNotExist as ex:
                return JsonResponse({"Message": "Old Bukht is not available in this telecommunication center."},
                                    status=500)
            old_order.status_id = old_port_status_id
            old_order.username = 'NULL'
            old_order.ranjePhoneNumber = 'NULL'
            try:
                new_order = Order.objects.get(telecom_id=telecom_id, telco_row=new_telco_row,
                                              telco_column=new_telco_column,
                                              telco_connection=new_telco_connection)
            except ObjectDoesNotExist as ex:
                return JsonResponse({"Message": "New Bukht is not available in this telecommunication center."},
                                    status=500)
            new_order.status_id = new_port_status_id
            new_order.username = username
            new_order.ranjePhoneNumber = ranjePhoneNumber
            old_order.save()
            new_order.save()
            return JsonResponse({"username": str(new_order.username), "status": str(new_order.status),
                                 "telecom": str(new_order.telecom), "telecom_id": str(new_order.telecom_id)},
                                status=200)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)}, status=500)


class GetOrdrPortInfo(views.APIView):
    def get(self, request, format=None):
        try:
            username = request.query_params.get('username')
            order_port = Order.objects.get(username=username)

            return JsonResponse({"username": str(order_port.username), "status": str(order_port.status),
                                 "telecom": str(order_port.telecom), "telecom_id": str(order_port.telecom_id)})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetCaptchaAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            get_captcha()
            with open('/home/sajad/Project/portmanv3/portman_web/classes/screenshot.png', 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetCitiesFromPratakAPIView(views.APIView):

    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            table_name = '"partak_telecom"'
            url = 'https://my.pishgaman.net/api/pte/getProvinceList'
            url_response = requests.get(url, headers={"Content-Type": "application/json"})
            response = url_response.json()
            print(response['ProvinceList'])
            for item in response['ProvinceList']:
                p_url = 'https://my.pishgaman.net/api/pte/getCityList?ProvinceID={}'.format(item['ProvinceID'])
                p_url_response = requests.get(p_url, headers={"Content-Type": "application/json"})
                p_response = p_url_response.json()
                for item2 in p_response['CityList']:
                    p_url = 'https://my.pishgaman.net/api/pte/getMdfList?CityID={}'.format(item2['CityID'])
                    p_url_response = requests.get(p_url, headers={"Content-Type": "application/json"})
                    p_response = p_url_response.json()
                    for item3 in p_response['MdfList']:
                        query = "INSERT INTO public.{} VALUES ({}, '{}', '{}', '{}', '{}', '{}');".format(table_name,
                                                                                                          item[
                                                                                                              'ProvinceID'],
                                                                                                          item[
                                                                                                              'ProvinceName'],
                                                                                                          item2[
                                                                                                              'CityID'],
                                                                                                          item2[
                                                                                                              'CityName'],
                                                                                                          item3[
                                                                                                              'MdfID'],
                                                                                                          item3[
                                                                                                              'MdfName'])
                        cursor = connection.cursor()
                        cursor.execute(query)

            # url = 'https://my.pishgaman.net/api/pte/getCityList?ProvinceID={0}'.format(username)
            # url_response = requests.get(url, headers={"Content-Type": "application/json"})
            # response = url_response.json()
            # print(response)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as ex:
            print(ex)
            return Response(str(ex), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FarzaneganScrappingAPIView(views.APIView):
    def post(self, request, format=None):
        data = request.data
        print(data)
        username = data['username']
        password = data['password']
        owner_username = data['owner_username']
        try:
            result = '' #farzanegan_scrapping(username, password, owner_username)
            if result is None:
                return Response({'result': 'Please try again!'})
            return Response({'result': result})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class DDRPageViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = DDRPageSerializer
    #pagination_class = LargeResultsSetPagination
    queryset = FarzaneganTDLTE.objects.all()

    def get_serializer(self, *args, **kwargs):
        if self.request.user.is_superuser:
            print(self.request.user.type)
            return DDRPageSerializer(request=self.request, *args, **kwargs)
        elif self.request.user.type_contains(SUPPORT):
            print(self.request.user.type)
            _fields = ['date_key', 'provider', 'customer_msisdn', 'total_data_volume_income']
            return DDRPageSerializer(request=self.request, remove_fields=_fields, *args, **kwargs)
        else:
            print(self.request.user.type)
            _fields = ['date_key', 'provider', 'customer_msisdn', 'total_data_volume_income']

            return DDRPageSerializer(request=self.request, remove_fields=_fields, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def current(self, request):
        serializer = DDRPageSerializer(request.user, request=request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user


class FarzaneganViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = FarzaneganTDLTE.objects.all().order_by('-date_key')
    permission_classes = (IsAuthenticated,)
    serializer_class = FarzaneganSerializer

    def get_queryset(self):
        queryset = self.queryset
        owner_username = self.request.query_params.get('owner_username', None)
        print(owner_username)
        if owner_username:
            print(owner_username)
            queryset = queryset.filter(owner_username=owner_username)

        return queryset


class FarzaneganExportExcelAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            owner_username = request.GET.get('owner_username', None)
            print(owner_username)
            farzanegan_tdlte = FarzaneganTDLTE.objects.filter(owner_username=owner_username).values()
            return Response({'result': farzanegan_tdlte})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class FarzaneganProviderDataAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            owner_username = request.GET.get('owner_username', None)
            print(owner_username)
            provider = FarzaneganTDLTE.objects.filter(owner_username=owner_username).first()
            farzanegan_provider_data = FarzaneganProviderData.objects.filter(provider_id=provider.provider_id).order_by(
                '-created').values().first()
            print(farzanegan_provider_data)
            return Response({'result': farzanegan_provider_data})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


class GetPartakProvincesAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            url = 'https://my.pishgaman.net/api/pte/getProvinceList'
            url_response = requests.get(url, headers={"Content-Type": "application/json"})
            response = url_response.json()
            print(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetPartakCitiesByProvinceIdAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            province_id = request.GET.get('province_id', None)
            url = 'https://my.pishgaman.net/api/pte/getCityList?ProvinceID={}'.format(province_id)
            url_response = requests.get(url, headers={"Content-Type": "application/json"})
            response = url_response.json()
            print(url_response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetPartakTelecomsByCityIdAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            city_id = request.GET.get('city_id', None)
            url = 'https://my.pishgaman.net/api/pte/getMdfList?CityID={}'.format(city_id)
            url_response = requests.get(url, headers={"Content-Type": "application/json"})
            response = url_response.json()
            print(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetPartakDslamListByTelecomIdAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            mdf_id = request.GET.get('mdf_id', None)
            url = 'https://my.pishgaman.net/api/pte/getDslamList?MdfID={}'.format(mdf_id)
            url_response = requests.get(url, headers={"Content-Type": "application/json"})
            response = url_response.json()
            print(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class UpdatePartakFqdnAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            mdf_id = request.GET.get('mdf_id', None)
            slat = request.GET.get('slat', None)
            fqdn = request.GET.get('fqdn', None)
            url = 'https://my.pishgaman.net/api/pte/updateFqdn?MdfID={}&Slat={}&NewFQDN={}'.format(mdf_id, slat, fqdn)
            url_response = requests.get(url, headers={"Content-Type": "application/json"})
            response = url_response.json()
            print(response)
            return Response(response, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class SaveNoteAPIView(views.APIView):
    def post(self, request):
        try:
            data = request.data
            province = data.get('province')
            city = data.get('city')
            telecom_center = data.get('telecom_center')
            problem_desc = data.get('problem_desc')
            username = self.request.user.username
            PishgamanNote.objects.create(province=province, city=city, telecom_center=telecom_center,
                                         problem_desc=problem_desc, username=username, status=0)
            return Response({"result": "New Note Successfully Added."})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetNotesViewSet(mixins.ListModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    #queryset = PishgamanNote.objects.all().order_by('-register_time')
    serializer_class = GetNotesSerializer
    #pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        queryset = PishgamanNote.objects.all().order_by('-register_time')
        note_id = self.request.query_params.get('note_id', None)
        not_username = self.request.query_params.get('not_username', None)
        not_telecom_center = self.request.query_params.get('not_telecom_center', None)
        not_problem_desc = self.request.query_params.get('not_problem_desc', None)
        note_status = self.request.query_params.get('status', None)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size

        if note_id:
            queryset = queryset.filter(id=note_id)
        if not_username:
            queryset = queryset.filter(username__icontains=not_username)
        if not_telecom_center:
            queryset = queryset.filter(telecom_center__icontains=not_telecom_center)
        if not_problem_desc:
            queryset = queryset.filter(problem_desc__icontains=not_problem_desc)

        if note_status:
            queryset = queryset.filter(status=note_status)
        return queryset.exclude(status__lt=0).order_by('status', '-register_time')

    @action(detail=False, methods=["patch"], url_path='change-status')
    def change_status(self, request, pk=None):
        try:
            note_obj = PishgamanNote.objects.get(id=pk)
            note_status = self.request.data['status']
            old_status = note_obj.status
            note_obj.status = note_status
            if int(note_status) == 1:
                note_obj.done_time = datetime.now()
            else:
                note_obj.done_time = None
            note_obj.save()
            description = f"old_status = {old_status}, new_status = {note_status}"
            self.save_log(note_obj.id, description)
            serializer = GetNotesSerializer(note_obj)
            return JsonResponse({'results': serializer.data}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

    def save_log(self, note_id, description):
        operator = self.request.user
        PishgamanNoteLog.objects.create(operator=operator, note_id=note_id, action='update', description=description)

    @never_cache
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, request=self.request)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            add_audit_log(request, 'Note', instance.id, 'Delete Note')
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as ex:
            print(ex)


class GetUncompletedRoutersBackup(views.APIView):
    def get(self, request, format=None):
        try:
            path_for_read = MIKROTIK_ROUTER_BACKUP_PATH
            path_for_write = '/var/portman_backup/'
            back_files = [f for f in os.listdir(path_for_read) if
                          os.path.isfile(os.path.join(path_for_read, f)) and '@' in f and 'Error' not in f]
            routers_info = []
            for item in back_files:
                print(item)
                path = path_for_read + item
                with open(path, 'r') as file:
                    if os.stat(path).st_size > 0:
                        last_line = file.readlines()[-1]
                        if 'use-radius=yes' not in last_line:
                            ip = item.split('@')[1].split('_')[0]
                            fqdn = item.split('@')[0]
                            date = item.split('@')[1].split('_', 1)[1].replace('.txt', '').replace('_', '-').replace(' ', '-').replace(':', '-')
                            date = datetime.strptime(date, '%Y-%m-%d-%H-%M-%S')
                            router_info = (ip, fqdn, date)
                            routers_info.append(router_info)

            incomplete_routers_info = sorted(routers_info, key=lambda x: x[2], reverse=True)
            file_name = f"{path_for_write}mikrotik_routers_uncompleted_backup_{datetime.strftime(datetime.now(), '%Y %m %d, %H:%M:%S')}.csv"
            with open(file_name, 'w') as file:
                csv_file = csv.writer(file)
                csv_file.writerow(['ip', 'fqdn', 'date'])
                for row in incomplete_routers_info:
                    csv_file.writerow(row)
            return JsonResponse(dict(result=f"File created successfully in ({file_name})."), status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class LocationServicesAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request):
        try:
            params = self.request.query_params
            location_srvice_obj = LocationServices()
            return JsonResponse(dict(result=location_srvice_obj.get_data_location(params)), status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def post(self, request):
        try:
            print('ooooooooooooooooooooooooooooooooooooooooooo')
            print('Created!!!!!!!!!!!!!!')
            params = request.data
            location_srvice_obj = LocationServices()
            return JsonResponse(dict(result=location_srvice_obj.create_data_location(params)), status=status.HTTP_201_CREATED)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def delete(self, request):
        try:
            params = self.request.query_params
            location_srvice_obj = LocationServices()
            return JsonResponse(dict(result=location_srvice_obj.delete_data_location(params)),
                                status=status.HTTP_204_NO_CONTENT)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def put(self, request):
        try:
            print('ooooooooooooooooooooooooooooooooooooooooooo')
            print('Updated!!!!!!!!!!!!!!')

            params = request.data
            location_srvice_obj = LocationServices()
            edit_result = location_srvice_obj.update_data_location(params)
            if edit_result['status'] == 200:
                return JsonResponse(dict(result=edit_result['result']),
                                    status=status.HTTP_200_OK)
            else:
                return JsonResponse(dict(result=edit_result['result']),
                                    status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class LocationServicesV2APIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request):
        try:
            params = self.request.query_params
            location_srvice_obj = LocationServicesV2()
            return JsonResponse(dict(result=location_srvice_obj.get_data_location(params)), status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def post(self, request):
        try:
            params = request.data
            location_srvice_obj = LocationServicesV2()
            return JsonResponse(dict(result=location_srvice_obj.create_data_location(params)), status=status.HTTP_201_CREATED)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def delete(self, request):
        try:
            params = self.request.query_params
            location_srvice_obj = LocationServicesV2()
            return JsonResponse(dict(result=location_srvice_obj.delete_data_location(params)),
                                status=status.HTTP_204_NO_CONTENT)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def put(self, request):
        try:
            params = request.data
            location_srvice_obj = LocationServicesV2()
            edit_result = location_srvice_obj.update_data_location(params)
            if edit_result['status'] == 200:
                return JsonResponse(dict(result=edit_result['result']),
                                    status=status.HTTP_200_OK)
            else:
                return JsonResponse(dict(result=edit_result['result']),
                                    status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


class GetStaticLocations(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request):
        try:
            location_srvice_obj = LocationServicesV2()
            return JsonResponse(dict(result=location_srvice_obj.get_static_locations()), status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '///' + str(exc_tb.tb_lineno)})



class GetDatatLocationsLoggingViewSet(viewsets.GenericViewSet,
                                      mixins.ListModelMixin,
                                      mixins.RetrieveModelMixin):
    serializer_class = GetDataLocationsLoggingSerializer
    permission_classes = (IsAuthenticated,)
    queryset = DataLocationsLog.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        username = self.request.query_params.get('username', None)
        log_action = self.request.query_params.get('action', None)
        ip = self.request.query_params.get('ip', None)
        log_status = self.request.query_params.get('status', None)
        if username:
            queryset = queryset.filter(username__iexact=username).order_by('-log_date') | DataLocationsLog.objects.filter(username__iexact='0'+username).order_by('-log_date')
        if log_action:
            queryset = queryset.filter(action__iexact=log_action)
        if ip:
            queryset = queryset.filter(new_ip__contains=ip) | queryset.filter(old_ip__contains=ip)
        if log_status:
            queryset = queryset.filter(status__iexact=log_status)
        return queryset


class TechnicalProfileViewSet(viewsets.GenericViewSet,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated, CanViewTechnicalProfileList)
    queryset = TechnicalProfile.objects.all()
    serializer_class = TechnicalProfileSerializer

    def get_queryset(self):
        queryset = self.queryset
        host = self.request.query_params.get('host', None)
        host_id = self.request.query_params.get('host_id', None)
        item = self.request.query_params.get('item', None)
        item_id = self.request.query_params.get('item_id', None)
        service = self.request.query_params.get('service', None)
        category = self.request.query_params.get('category', None)
        username = self.request.query_params.get('username', None)
        created_by = self.request.query_params.get('created_by', None)
        page_size = self.request.query_params.get('page_size', 10)

        if item:
            queryset = queryset.filter(item__icontains=item)

        if item_id:
            queryset = queryset.filter(item_id__icontains=item_id)

        if host:
            queryset = queryset.filter(host__icontains=host)

        if host_id:
            queryset = queryset.filter(host_id__icontains=host_id)

        if service:
            queryset = queryset.filter(service__icontains=service)

        if category:
            queryset = queryset.filter(category__icontains=category)

        if username:
            queryset = queryset.filter(technical_user__username__icontains=username)

        if created_by:
            queryset = queryset.filter(created_by__username__icontains=created_by)

        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = page_size
        
        return queryset

    def create(self, request, *args, **kwargs):
        host_id = self.host_is_valid(request.data['host'])
        if not host_id:
            raise ValidationError(dict(results=f"The host you entered doesn't exist."
                                               f" Please make sure you enter the correct host."))
        item_id = self.item_is_valid(request.data['item'], host_id)
        if not item_id:
            raise ValidationError(dict(results=f"The item you entered doesn't exist."
                                               f" Please make sure you enter the correct item."))
        request.data['host'] = unidecode(request.data.get('host')).strip()
        request.data['host_id'] = host_id
        request.data['item'] = unidecode(request.data.get('item')).strip()
        request.data['item_id'] = item_id
        request.data['created_by'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        queryset = TechnicalProfile.objects.filter(item_id=serializer.validated_data['item_id']).exclude(
            deleted_at__isnull=False)
        if queryset.exists():
            raise ValidationError(dict(results="The item you entered has already been used. Please enter another item."))
        serializer.save()

    @action(detail=False, methods=["put"])
    def recalculate(self, request):
        login_url = 'http://api.pishgaman.net/gateway/token'
        response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                    "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                                                    "appid": "57"})
        response_json = response.json()
        send_message_url = f"http://api.pishgaman.net/gateway/system/job/dccustomer/{request.data.get('from_date')}/{request.data.get('to_date')}/"
        send_message_response = requests.put(send_message_url,
                                                headers={"Content-Type": "application/json",
                                                        "Authorization": "Bearer " + response_json['Result'],
                                                        "appid": "57"})
        send_message_response_json = send_message_response.json()

        if send_message_response_json.get('OperationResultCode') == 200:
            return Response({'results': "Successfully Requested", 'status': status.HTTP_200_OK}, status=status.HTTP_200_OK)
            
        return Response({'results': "Gateway did not respond properly", 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def host_is_valid(self, host):
        url = "https://monitoring2.pishgaman.net/api_jsonrpc.php"
        token = self.get_token()
        body = str({"jsonrpc": "2.0", "id": 1, "method": "host.get", "auth": f"{token}",
                "params": {
                    "output": ["hostid", "name", "host"],
                    "search": {"name": host},
                    "searchWildcardsEnabled": True
                }
                }).replace("'", '"').replace('True', 'true')
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=body)
        response_json = response.json()
        if len(response_json.get('result')) > 0:
            print(response_json.get('result')[0].get('hostid'))
            return response_json.get('result')[0].get('hostid')
        return False

    def item_is_valid(self, item, host_id):
        url = "https://monitoring2.pishgaman.net/api_jsonrpc.php"
        token = self.get_token()
        body = str({"jsonrpc": "2.0", "id": 1, "method": "item.get", "auth": f"{token}",
                    "params": {
                        "hostids": f"{host_id}",
                        "output": ["hostid", "name", "key_", "host"],
                        "search": {"name": f"{item}"},
                        "searchWildcardsEnabled": True}}).replace("'", '"').replace('True', 'true')

        response = requests.post(url, headers={"Content-Type": "application/json"}, data=body)
        response_json = response.json()
        if len(response_json.get('result')) > 0:
            return response_json.get('result')[0].get('itemid')
        return False

    def get_token(self):
        url = "https://monitoring2.pishgaman.net/api_jsonrpc.php"
        body = str({"jsonrpc": "2.0", "id": 1, "method": "user.login",
                    "params": {"user": "software", "password": "ASXRQKD78kykRLT"}}).replace("'", '"')
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=body, verify=False)
        return response.json().get('result')


class TechnicalUserViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, )
    queryset = TechnicalUser.objects.all()
    serializer_class = TechnicalUserSerializer

    def get_queryset(self):
        queryset = self.queryset
        username = self.request.query_params.get('username', None)
        page_size = self.request.query_params.get('page_size', 10)

        if username:
            queryset = queryset.filter(username__icontains=username)
        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['created_by'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        request.data['created_by'] = request.user.id
        print(instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        queryset = TechnicalUser.objects.filter(username=serializer.validated_data['username'],
                                                type=serializer.validated_data['type'],
                                                title=serializer.validated_data['title']).exclude(
            deleted_at__isnull=False)
        if queryset.exists():
            raise ValidationError(dict(results="The user that you are trying to create has already been created."))
        serializer.save()


class FarzaneganJobStatusAPIView(views.APIView):
    def get(self, request, format=None):
        try:
            now = datetime.now()
            running_day = now.strftime("%Y-%m-%d")
            latest_record = FarzaneganTDLTE.objects.latest('date_key')
            latest_record_date = latest_record.date_key
            return JsonResponse(dict(result=dict(latest_running_date=running_day, latest_record_date=latest_record_date)))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})
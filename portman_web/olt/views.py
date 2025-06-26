import sys, re, os
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.forms.models import model_to_dict
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status, views, permissions
from .serializers import *
from django.core import serializers
from django.db.models import Q
from .models import *
from dslam.models import City
from users.models import User as MainUser, ProvinceAccess
from users.serializers import ContactSerializer, UserSerializer as MainUserSerializer
from cartable.models import Ticket, TicketType, Reminder
from olt import utility
from rest_framework import pagination
from classes.persian import unidecode, standard_lat, standard_long
from classes.base_permissions import FTTH_WEB_SERVICE, ADMIN, FTTH_ADMIN, FTTH_OPERATOR, FTTH_INSTALLER, FTTH_CABLER, FTTH_TECH_AGENT
from classes.services.mini_services import convert_postal_code_to_geo_coordinate, convert_postal_code_to_address
from classes.services.pishgaman_geteway import PishgamanGeteway
from datetime import datetime, timedelta
from .services.devices_capacity import CheckCapacityService
from .services.nearest_location import NearestLocation, NearestCabinet, NearestFat, NearestUsers, NearestHandhole,\
    NearestEquipmentsFactory
from .services.mini_services import add_audit_log, fat_available_ports, splitter_available_ports,\
    get_first_port_from_fat, get_microduct_length, get_cable_length, reservdports_reports
from .services.city_equipment import CityEquipmentService
from .services.ftth_equipment import FatRelations
from .services.ticketer import Ticketer
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.db.models import Prefetch
import io, csv
import openpyxl
from django.http import HttpResponse
from .permissions import CanViewObjectsList, CanViewOltList, CanViewOltTypeList, CanViewOltCommandList, \
    CanViewReservedPorts, CanViewFatList, CanViewCableList
from .mixins import SetupOntMixin
from config.settings import OLT_BACKUP_PATH
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from .querysets.queryset_factory import QuerysetFactory
#from .signals import *
from .services.partak_web_service import PartakApi
from .services.reminders import CreateReminders
from .utility import set_current_user
import concurrent.futures
from django.utils.translation import gettext as _
PORTMAN_ENV = os.environ.get('PORTMAN_ENV', 'dev')


class OLTViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewOltList)
    serializer_class = OLTSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('olt', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        isFakeRequest = request.data.get('fake_request', False)
        request.data['fqdn'] = request.data.get('fqdn').lower()
        serializer = self.serializer_class(data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        if (isFakeRequest == False):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            description = f"Add OLT ID={serializer.data['id']}"
            add_audit_log(request, 'OLT', serializer.data['id'], 'Create', description)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response([], status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        self.edit_validator(instance)
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, request=self.request, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'OLT', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.delete_validator(instance)
        OLT.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete OLT ID={instance.id}"
        add_audit_log(request, 'OLT', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete_validator(self, instance):
        having_fat = instance.fat_set.filter(deleted_at__isnull=True).exists()
        if having_fat:
            raise ValidationError(dict(results=_("Deletion failed. "
                                               "This olt has associated fats that must be addressed before you can proceed. "
                                               "Please delete these fats first.")))

    def perform_create(self, serializer):
        queryset = OLT.objects.filter(name=serializer.validated_data['name'])
        if queryset.exists():
            raise ValidationError(dict(results=f"The OLT {serializer.validated_data['name']} has already created!"))
        available_cabinet_capacity = CheckCapacityService.get_device_available_capacity('cabinet',
            serializer.validated_data['cabinet'].id).get('available_capacity')
        if available_cabinet_capacity <= 0:
            raise ValidationError(dict(results="There isn't free capacity for the selected cabinet!!"))
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()

    @action(detail=True, methods=['get'], url_path='backup-files')
    def backup_files(self, request, pk=None):
        olt = self.get_object()
        olt_type = olt.olt_type.model
        olt_fqdn = olt.fqdn
        olt_ip = olt.ip
        if olt_type == 'olt_zyxel':
            return JsonResponse({'response': 'Not found.'}, status=status.HTTP_400_BAD_REQUEST)
        backup_path = OLT_BACKUP_PATH + olt_type + '/'
        try:
            date_array = []
            for i in range(0, 10):
                date_array.append(str(datetime.now().date() - timedelta(i)))
            filenames = []
            for filename in os.listdir(backup_path):
                if filename.__contains__(olt_fqdn) or filename.__contains__(olt_ip):
                    for item in date_array:
                        if item in filename:
                            file_info = dict(file_name=filename, file_date=filename.split('_')[1].split('.')[0])
                            filenames.append(file_info)
            return JsonResponse({'response': json.dumps(filenames, default=lambda o: o.__dict__,
                                                        sort_keys=True, indent=4)})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

    @action(detail=True, methods=['post'], url_path='download-backup')
    def download_backup(self, request, pk=None):
        try:
            olt = self.get_object()
            olt_type = olt.olt_type.model
            file_name = self.request.data.get('file_name')
            if olt_type == 'olt_zyxel':
                return JsonResponse({'response': 'Not found.'}, status=status.HTTP_400_BAD_REQUEST)
            backup_path = OLT_BACKUP_PATH + olt_type + '/'
            backup_path = backup_path + file_name
            f = open(backup_path, "r")
            return JsonResponse({'response': f.read()})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return JsonResponse({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})

    def edit_validator(self, instance):
        if instance.cabinet.id != self.request.data.get('cabinet'):
            if instance.fat_set.filter(deleted_at__isnull=True).exists():
                raise ValidationError(dict(results="You can't change cabinet for this olt because it has fat."))


class OltCardViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewOltList)
    serializer_class = OltCardSerializer

    def get_queryset(self):
        olt_id = self.kwargs.get('olt_id')
        queryset = OltCard.objects.filter(olt__id=olt_id).exclude(deleted_at__isnull=False)
        queryset = queryset.order_by('number')
        pagination.PageNumberPagination.page_size = len(queryset)

        return queryset

    def create(self, request, *args, **kwargs):
        olt_id = self.kwargs.get('olt_id')
        request.data['olt_id'] = olt_id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, olt_id)
        headers = self.get_success_headers(serializer.data)
        description = f"Add OltCard ID={serializer.data['id']}"
        add_audit_log(request, 'OltCard', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'OltCard', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        OltPort.objects.filter(card=instance).update(deleted_at=datetime.now())
        description = f"Delete OltCard ID={instance.id}"
        add_audit_log(request, 'OltCard', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer, olt_id):
        card_number = serializer.validated_data.get('number')
        is_exist = OltCard.objects.filter(olt__id=olt_id, number=card_number).exclude(deleted_at__isnull=False).exists()
        if is_exist:
            raise ValidationError(dict(results=f"Card number {card_number} has been defined."))
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()
        if obj.ports_count:
            for port in range(1, obj.ports_count+1):
                OltPort.objects.create(card=obj, port_number=port)

    def perform_update(self, serializer):
        card_number = serializer.validated_data.get('number')
        is_exist = OltCard.objects.filter(
            olt__id=serializer.instance.olt.pk, number=card_number).exclude(
            deleted_at__isnull=False).exclude(id=serializer.instance.pk).exists()
        if is_exist:
            raise ValidationError(dict(results=f"Card number {card_number} has been defined."))
        serializer.save()
        
    @action(detail=False, methods=["post"])
    def saveall(self, request, *args, **kwargs):
        olt_id = self.kwargs.get('olt_id')
        cards = self.request.data['cards']
        for card in cards:
            is_exist = OltCard.objects.filter(olt__id=olt_id, number=card['number']).exists()
            if is_exist:
                raise ValidationError(dict(results=f"Card number {card['number']} has been defined."))
            card['olt_id'] = olt_id

        serializer = self.serializer_class(data=cards, many=True)
        if serializer.is_valid():
            serializer.save()
        for card in serializer.instance:
            for port in range(1, card.ports_count + 1):
                OltPort.objects.create(card=card, port_number=port)

        return Response(self.request.data, status=status.HTTP_201_CREATED)


class OltPortViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewOltList)
    serializer_class = OltPortSerializer

    def get_queryset(self):
        card_number = self.kwargs.get('card_number')
        olt_id = self.kwargs.get('olt_id')
        queryset = OltPort.objects.filter(card__number=card_number, card__olt__id=olt_id).exclude(deleted_at__isnull=False)
        queryset = queryset.order_by('port_number')
        pagination.PageNumberPagination.page_size = len(queryset)

        return queryset

    def create(self, request, *args, **kwargs):
        card_number = self.kwargs.get('card_number')
        olt_id = self.kwargs.get('olt_id')
        card_obj = OltCard.objects.filter(olt__id=olt_id, number=card_number).exclude(deleted_at__isnull=False)
        if not card_obj:
            raise ValidationError(dict(results=f"card number {card_number} is not defined. "
                                               f"Please define the card number and then try again."))

        is_exist = OltPort.objects.filter(port_number=request.data.get('port_number'),
                                          card__olt__id=olt_id,
                                          card__number=card_number).exclude(deleted_at__isnull=False).exists()
        if is_exist:
            raise ValidationError(dict(results=f"Port number {request.data.get('port_number')} has been defined."))

        pp_is_used = OltPort.objects.filter(patch_panel_port__id=request.data.get('pp_port_id')).exclude(deleted_at__isnull=False)
        if pp_is_used:
            raise ValidationError(dict(results=f"Selected patch panel port has been already used."))

        request.data['card_id'] = card_obj.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add OltPort ID={serializer.data['id']}"
        add_audit_log(request, 'OltPort', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        card_number = self.kwargs.get('card_number')
        olt_id = self.kwargs.get('olt_id')
        card_obj = OltCard.objects.filter(olt__id=olt_id, number=card_number).exclude(deleted_at__isnull=False)
        if not card_obj:
            raise ValidationError(dict(results=f"card number {card_number} is not defined. "
                                               f"Please define the card number and then try again."))

        request.data['card_id'] = card_obj.id
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        is_exist = OltPort.objects.filter(port_number=request.data.get('port_number'),
                                          card__olt__id=olt_id,
                                          card__number=card_number).exclude(deleted_at__isnull=False).exclude(id=instance.pk).exists()
        if is_exist:
            raise ValidationError(dict(results=f"Port number {request.data.get('port_number')} has been defined."))

        pp_is_used = OltPort.objects.filter(
            patch_panel_port__id=request.data.get('pp_port_id')).exclude(
            deleted_at__isnull=False).exclude(
            id=instance.pk).exists()
        if pp_is_used:
            raise ValidationError(dict(results=f"Selected patch panel port has been already used."))

        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'OltPort', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        description = f"Delete OltPort ID={instance.id}"
        add_audit_log(request, 'OltPort', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()
        if obj.ports_count:
            for port in range(1, obj.ports_count + 1):
                OltPort.objects.create(card=obj, port_number=port)

    @action(detail=False, methods=["post"])
    def saveall(self, request, *args, **kwargs):
        ports = self.request.data['ports']
        card_number = self.kwargs.get('card_number')
        olt_id = self.kwargs.get('olt_id')
        card_obj = OltCard.objects.filter(olt__id=olt_id, number=card_number).exclude(deleted_at__isnull=False).first()

        if not card_obj:
            raise ValidationError(dict(results=f"card number {card_number} is not defined. "
                                               f"Please define the card number and then try again."))
        def get_pp_port(port):
            if port.get('pp_port_id', None):
                patch_panel_port = TerminalPort.objects.get(pk=port['pp_port_id'])
            else:
                patch_panel_id = port['pp_id']
                cassette_number = port['pp_cassette_number']
                port_number = port['pp_port_number']
                patch_panel_port = TerminalPort.objects.get(terminal__id=patch_panel_id,
                                                            cassette_number=cassette_number,
                                                            port_number=port_number)
            return patch_panel_port

        for port in ports:
            port_obj = OltPort.objects.get(port_number=port['port_number'], card=card_obj)
            if not port.get('pp_port_id', None) and not port.get('pp_id', None):
                port_obj.patch_panel_port = None
                port_obj.save()
                ports.remove(port)
                continue
            patch_panel_port = get_pp_port(port)
            ppp_is_used = OltPort.objects.filter(patch_panel_port=patch_panel_port).exclude(deleted_at__isnull=False).exclude(pk=port_obj.id).first()
            if ppp_is_used:
                raise ValidationError(dict(results=f"Selected patch panel port at port {ppp_is_used.port_number} has been already used."))

        for port in ports:
            port_obj = OltPort.objects.get(port_number=port['port_number'], card=card_obj)
            port_obj.patch_panel_port = get_pp_port(port)
            port_obj.save()

        return Response(self.request.data, status=status.HTTP_201_CREATED)


class BulkSaveOltPortsAPIView(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)

    def post(self, request):
        try:
            def get_terminal_port(terminal_id, cassette_number, port_number):
                terminal_port = TerminalPort.objects.get(terminal__id=terminal_id,
                                                         cassette_number=cassette_number,
                                                         port_number=port_number)
                return terminal_port
            ports = self.request.data['ports']
            for port in ports:
                olt_port_number = port['olt_info']['port_number']
                olt_card_number = port['olt_info']['card_number']
                olt_id = port['olt_info']['olt']
                olt_port_obj = OltPort.objects.filter(port_number=olt_port_number,
                                                      card__olt__id=olt_id,
                                                      card__number=olt_card_number).first()
                if not port.get('terminal_info', None):
                    olt_port_obj.patch_panel_port = None
                    olt_port_obj.save()
                    #ports.remove(port)
                    continue
                terminal_id = port['terminal_info']['terminal']
                cassette_number = port['terminal_info']['cassette_number']
                port_number = port['terminal_info']['port_number']
                terminal_port = get_terminal_port(terminal_id, cassette_number, port_number)
                terminal_port_is_used = OltPort.objects.filter(patch_panel_port=terminal_port).exclude(
                    deleted_at__isnull=False).exclude(pk=olt_port_obj.id).first()
                if terminal_port_is_used:
                    return Response(dict(results=f"Selected patch panel port for port {olt_port_number} has been already used.",
                                         port_info=port),
                                         status=status.HTTP_400_BAD_REQUEST)
            for port in ports:
                if not port.get('terminal_info', None):
                    continue

                olt_port_number = port['olt_info']['port_number']
                olt_card_number = port['olt_info']['card_number']
                olt_id = port['olt_info']['olt']
                olt_port_obj = OltPort.objects.filter(port_number=olt_port_number,
                                                      card__olt__id=olt_id,
                                                      card__number=olt_card_number).first()

                terminal_id = port['terminal_info']['terminal']
                cassette_number = port['terminal_info']['cassette_number']
                port_number = port['terminal_info']['port_number']
                terminal_port = get_terminal_port(terminal_id, cassette_number, port_number)
                olt_port_obj.patch_panel_port = terminal_port
                olt_port_obj.save()
                
            return Response(self.request.data, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)}, status=status.HTTP_400_BAD_REQUEST)


class OLTCommandsAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def post(self, request):
        device_ip = str(get_device_ip(request))
        data = request.data
        fqdn = data.get('fqdn', None)
        olt_id = request.data.get('olt_id', None)
        if olt_id is None:
            olt_id = OLT.objects.get(fqdn=str(fqdn).lower()).id
        olt_obj = OLT.objects.get(id=olt_id)
        command = data.get('command', None)
        # command = command_recognise(command)
        params = data.get('params', None)
        olt_type = olt_obj.olt_type_id
        try:
            result = utility.olt_run_command(olt_obj.pk, command, params)
            description = dict(ip=olt_obj.ip, fqdn=olt_obj.fqdn, command=command, result=result,
                               port_conditions=params.get('port_conditions', None))
            add_audit_log(request, 'OLT', olt_id, 'RunCommand', str(description))
            return JsonResponse(dict(response=result), status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})


class OLTCommandViewSet(mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = OLTCommandSerializer
    permission_classes = (IsAuthenticated, CanViewOltCommandList)
    # pagination_class = MediumResultsSetPagination

    def get_queryset(self):
        queryset = OLTCommand.objects.all()
        olt_id = self.request.query_params.get('olt_id', None)
        command_name = self.request.query_params.get('command_name', None)
        page_size = self.request.query_params.get('page_size', 100)

        if olt_id:
            olt_type = OLT.objects.get(id=olt_id).olt_type_id
            allowed_commands_olt_type = OLTTypeCommand.objects.filter(olt_type=olt_type).values_list(
            'command', flat=True)
            queryset = queryset.filter(id__in=allowed_commands_olt_type)
        if command_name:
            queryset = queryset.filter(text__icontains=command_name)
        pagination.PageNumberPagination.page_size = page_size
        return queryset.order_by('id')


class OLTCabinetTypeViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = CabinetTypeSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('cabinet_type', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        is_odc = self.request.query_params.get('is_odc', False)
        pagination.PageNumberPagination.page_size = page_size

        if is_odc:
            queryset = queryset.filter(is_odc=(is_odc == 'true'))

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add cabinet type ID={serializer.data['id']}"
        add_audit_log(request, 'CabinetType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'CabinetType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        description = f"Delete cabinet type ID={instance.id}"
        add_audit_log(request, 'CabinetType', instance.id, 'Delete', description)
        # self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        queryset = OLTCabinetType.objects.filter(model=serializer.validated_data['model']).exclude(deleted_at__isnull=False)
        if queryset.exists():
            raise ValidationError(dict(results=f"The cabinet type with model {serializer.validated_data['model']}"
                                               f" has already created!"))
        serializer.save()


class OLTCabinetViewSet(viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = OLTCabinetSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('cabinet', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        request_from_map = self.request.query_params.get('request_from_map', None)
        if request_from_map:
            page_size = 1000 #len(queryset)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_current_user(request.user)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add cabinet ID={serializer.data['id']}"
        add_audit_log(request, 'Cabinet', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'Cabinet', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.delete_validator(instance)
        OLTCabinet.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete cabinet ID={instance.id}"
        add_audit_log(request, 'Cabinet', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete_validator(self, instance):
        having_olt = instance.olt_set.filter(deleted_at__isnull=True).exists()
        having_cable = (Cable.objects.filter(Q(Q(src_device_type='cabinet') | Q(src_device_type='odc'), src_device_id=instance.id)
                                            | Q(Q(dst_device_type='cabinet') | Q(dst_device_type='odc'), dst_device_id=instance.id))
                        .exclude(deleted_at__isnull=False).exists())

        if having_olt:
            raise ValidationError(dict(results=_("Deletion failed. "
                                               "It has associated olts that must be addressed before you can proceed. "
                                               "Please delete these olts first.")))
        if having_cable:
            raise ValidationError(dict(results=_("Deletion failed. "
                                                 "It has associated cables that must be addressed before you can proceed. "
                                                 "Please delete these cables first.")))


    def perform_create(self, serializer):
        with transaction.atomic():
            obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(OLTCabinet),
                                                   object_id=0,
                                                   creator=self.request.user)
            obj = serializer.save(property=obj_property)
            obj_property.object_id = obj.id
            obj_property.save()


    @action(detail=True, methods=["get"])
    def fats(self, request, pk=None):
        try:
            page_size = self.request.query_params.get('page_size', 10)
            cabinet = self.get_object()
            fats = FAT.objects.filter(olt__cabinet=cabinet).exclude(deleted_at__isnull=False)
            paginator = PageNumberPagination()
            paginator.page_size = page_size
            paginated_fats = paginator.paginate_queryset(fats, request)

            return paginator.get_paginated_response(FATSerializer(paginated_fats, many=True).data)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})


class FATViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, CanViewFatList)
    serializer_class = FATSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('fat', self.request)
        page_size = self.request.query_params.get('page_size', 100)
        request_from_map = self.request.query_params.get('request_from_map', None)

        if self.request.user.type_contains(FTTH_WEB_SERVICE):
            page_size = 100 #len(queryset)
            self.serializer_class = FATSerializerMini

        if request_from_map:
            page_size = 1000 #len(queryset)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def _get_capacity_by_type(self, type_id):
        type = FATType.objects.get(id=int(type_id))
        if type is None:
            return 8
        return type.port_count

    def create(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        # request.data['max_capacity'] = self._get_capacity_by_type(request.data.get('fat_type'))
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_current_user(request.user)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add FAT ID={serializer.data['id']}"
        add_audit_log(request, 'FAT', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        # request.data['max_capacity'] = self._get_capacity_by_type(request.data.get('fat_type'))
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'FAT', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.delete_validator(instance)
        FAT.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete FAT ID={instance.id}"
        add_audit_log(request, 'FAT', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete_validator(self, instance):
        having_splitter = instance.fat_set.filter(deleted_at__isnull=True).exists()
        having_user = instance.reservedports_set.filter(status__in=ReservedPorts.NOT_FREE_STATUZ)
        having_subset = instance.fat_set.filter(deleted_at__isnull=True).exists()
        having_cable = (
            Cable.objects.filter(Q(src_device_type='fat', src_device_id=instance.id)
                                 | Q(dst_device_type='fat'), dst_device_id=instance.id)).exclude(deleted_at__isnull=False).exists()
        
        if having_splitter or having_subset:
            raise ValidationError(dict(results=_("Deletion failed. "
                                               "It has associated items like splitter, ffat, otb or tb. "
                                               "Please delete these items first.")))

        if having_cable:
            raise ValidationError(dict(results=_("Deletion failed. "
                                                 "It has associated cables that must be addressed before you can proceed. "
                                                 "Please delete these cables first.")))
        if having_user:
            raise ValidationError(dict(results=_("Deletion failed. "
                                                 "It has associated users that must be addressed before you can proceed. "
                                                 "Please delete these users first.")))

        if PORTMAN_ENV == 'prod':
            response, payload, url = PartakApi(instance).deleteFAT()
            error_code = response.get('ResponseStatus', {}).get('ErrorCode')
            if error_code not in [0, 2332]:
                CreateReminders.partak_api_error(response, payload, url)
                message = response.get('ResponseStatus', {}).get('Message')
                raise ValidationError(dict(results=_(f"Partak Error. {message}")))

    def check_partak_response(self, response, payload, url):
        if response.get('ResponseStatus', {}).get('ErrorCode') != 0:
            CreateReminders.partak_api_error(response, payload, url)
            return 'Failed'
        return 'Success'

    # def create_in_partak(self, instance):
    #     response, payload, url = PartakApi(instance).createFAT()
    #     response_status = self.check_partak_response(response, payload, url)
    #     if response_status == 'Failed':
    #         message = response.get('ResponseStatus', {}).get('Message')
    #         raise ValidationError(dict(results=_(f"Partak Error. {message}")))

    def edit_in_partak(self, instance):
        response, payload, url = PartakApi(instance).createFAT()
        self.check_partak_response(response, payload, url)
        response, payload, url = PartakApi(instance).updateFAT()
        response_status = self.check_partak_response(response, payload, url)
        if response_status == 'Failed':
            message = response.get('ResponseStatus', {}).get('Message')
            raise ValidationError(dict(results=_(f"Partak Error. {message}")))

    def perform_create(self, serializer):
        
        # available_fat_capacity = CheckCapacityService.get_device_available_capacity('olt',
        #     serializer.validated_data['olt'].id).get('available_capacity')
        # if available_fat_capacity <= 0:
        #     raise ValidationError(dict(results="There isn't free capacity for the selected OLT!!"))

        if self.request.data.get('parent') != None:
            if not self.request.data.get('fat_splitter', None):
                if FAT.objects.filter(patch_panel_port__id=self.request.data.get('patch_panel_port')).exclude(deleted_at__isnull=False):
                    raise ValidationError(dict(results="The selected patch panel port has been already used."))
            else:
                if FAT.objects.filter(parent__id=self.request.data.get('parent'),
                                      fat_splitter__id=self.request.data.get('fat_splitter'),
                                      leg_number=int(self.request.data.get('leg_number'))).\
                                     exclude(deleted_at__isnull=False).exclude(splitter__isnull=True):
                    raise ValidationError(dict(results="The selected splitter leg number has been already used."))

        with transaction.atomic():
            obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(FAT),
                                                   object_id=0,
                                                   creator=self.request.user)
            obj = serializer.save(property=obj_property)
            obj_property.object_id = obj.id
            obj_property.save()
            # if PORTMAN_ENV == 'prod' and not obj.is_otb and not obj.is_tb:
            #     self.create_in_partak(obj)

    def perform_update(self, serializer):
        instance = self.get_object()
        patch_panel_port = self.request.data.get('patch_panel_port')
        fat_splitter = self.request.data.get('fat_splitter')

        if self.request.data.get('parent') is not None: ## updating ffat
            if patch_panel_port:
                used_fat = FAT.objects.filter(patch_panel_port__id=patch_panel_port).exclude(pk=instance.pk).exclude(deleted_at__isnull=False).first()
                if used_fat:
                    raise ValidationError(dict(results=f"Cassette {patch_panel_port.cassette_number} "
                                                       f"Port {patch_panel_port.port_number} has been already used in fat code {used_fat.code}"))
            if fat_splitter:
                used_fat = FAT.objects.filter(parent__id=self.request.data.get('parent'),
                                              fat_splitter__id=fat_splitter,
                                              leg_number=int(self.request.data.get('leg_number'))). \
                        exclude(deleted_at__isnull=False).exclude(splitter__isnull=True).exclude(pk=instance.pk)
                if used_fat:
                    raise ValidationError(dict(results=f"The selected splitter leg number has been already used in fat code {used_fat.code}."))

        with transaction.atomic():
            instance = serializer.save()
            if PORTMAN_ENV == 'prod' and not instance.is_otb and not instance.is_tb and instance.property and instance.property.approved_at:
                self.edit_in_partak(instance)

    def generate_excel(self, queryset):
        # Create an Excel workbook
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "FAT List"

        # Add headers to the sheet (added cabinet_name and cabinet_crm_id)
        headers = [
            'ID', 'Name', 'Code', 'FAT Type', 'Is Active', 'Address', 'Parent',
            'Max Capacity', 'OLT', 'Cabinet Name', 'Cabinet CRM ID', 'Patch Panel Port',
            'Lat', 'Long', 'Province', 'City', 'Type'
        ]
        sheet.append(headers)

        # Write data rows
        for fat in queryset:
            # Data extraction with safe fallbacks
            parent_code = fat.parent.code if fat.parent else ''
            pp_port = fat.patch_panel_port.port_number if fat.patch_panel_port else ''
            city = fat.olt.cabinet.city if (fat.olt and fat.olt.cabinet and fat.olt.cabinet.city) else None
            province = city.parent.name if city and city.parent else None
            city_name = city.name if city else None
            fat_type = 'OTB' if fat.is_otb else ('FFAT' if fat.parent else 'FAT')

            # Get cabinet name and CRM ID
            cabinet_name = fat.olt.cabinet.name if fat.olt and fat.olt.cabinet else ''
            cabinet_crm_id = fat.olt.cabinet.crm_id if fat.olt and fat.olt.cabinet else ''

            # Append the row to the sheet
            sheet.append([
                fat.id, fat.name, fat.code, fat.fat_type.name, bool(fat.is_active), fat.address, parent_code,
                fat.max_capacity, fat.olt.name if fat.olt else '', cabinet_name, cabinet_crm_id, pp_port,
                fat.lat, fat.long, province, city_name, fat_type
            ])

        # Save the workbook to an in-memory stream
        with io.BytesIO() as output:
            wb.save(output)
            output.seek(0)
            return output.read()
    @action(detail=False, methods=["get"])
    def download_excel(self, request):
        try:
            # Check for user permissions
            if not request.user.type_contains([FTTH_ADMIN, FTTH_OPERATOR]):
                raise ValidationError({'results': "Access Denied"})

            # Get parameters
            province_id = request.GET.get('province_id')
            city_id = request.GET.get('city_id')

            # Fetch FAT objects with initial filters and use select_related for optimization
            queryset = FAT.objects.filter(deleted_at__isnull=True, is_tb=False) \
                .select_related('parent', 'fat_type', 'olt__cabinet__city', 'olt__cabinet',
                                'olt__cabinet__city__parent') \
                .prefetch_related('patch_panel_port')

            # Apply province and city filters if they exist
            if province_id:
                queryset = queryset.filter(olt__cabinet__city__parent_id=province_id)
            if city_id:
                queryset = queryset.filter(olt__cabinet__city_id=city_id)

            # Generate the Excel file in memory
            excel_data = self.generate_excel(queryset)

            # Create HTTP response with the excel file using StreamingHttpResponse for large datasets
            response = StreamingHttpResponse(
                io.BytesIO(excel_data),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="FAT_List.xlsx"'
            return response

        except ValidationError as e:
            return JsonResponse({'result': str(e)}, status=403)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'error': str(ex), 'file': fname, 'line': exc_tb.tb_lineno}, status=500)
    @action(detail=False, methods=["get"])
    def available_ports(self, request, pk=None):
        try:
            available_ports = fat_available_ports(pk)
            if type(available_ports) == str:
                return JsonResponse({'results': available_ports}, status=status.HTTP_204_NO_CONTENT)
            return JsonResponse({'results': available_ports}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

    @action(detail=False, methods=["get"])
    def first_port(self, request, pk=None):
        try:
            first_port = get_first_port_from_fat(pk)
            return JsonResponse({'results': first_port}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

    @action(detail=True, methods=["get"])
    def relations(self, request, pk=None):
        try:
            fat = self.get_object()
            fat_relations = FatRelations(fat)
            relations = fat_relations.get_relations()
            return JsonResponse({'results': relations}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

    @action(detail=True, methods=["get"])
    def childes(self, request, pk=None):
        ffat_list = []
        otb_list = []
        tb_list = []
        childes = list(FAT.objects.filter(parent=self.get_object(), deleted_at__isnull=True))
        all_childes = []

        while childes:
            all_childes.extend(childes)
            child_ids = [item.id for item in childes]
            childes = list(FAT.objects.filter(parent__in=child_ids, deleted_at__isnull=True))

        for item in all_childes:
            info = {
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'lat': item.lat,
                'lng': item.long
            }

            if item.building:
                info['buidling_info'] = {
                    'id': item.building.id,
                    'name': item.building.name,
                    'code': item.building.code
                }
            else:
                info['buidling_info'] = None

            if item.is_tb:
                tb_list.append(info)
            elif item.is_otb:
                otb_list.append(info)
            else:
                ffat_list.append(info)

        result = {
            'ffat_list': ffat_list,
            'otb_list': otb_list,
            'tb_list': tb_list
        }

        return JsonResponse({'results': result}, status=status.HTTP_200_OK)

class SplitterViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = SplitterSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('splitter', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def _get_capacity_by_type(self, type_id):
        type = SplitterType.objects.get(id=int(type_id))
        if type is None:
            return 32
        return type.legs_count

    def create(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        # request.data['space'] = unidecode(request.data.get('space'))
        request.data['max_capacity'] = self._get_capacity_by_type(request.data.get('splitter_type'))
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add splitter ID={serializer.data['id']}"
        add_audit_log(request, 'Splitter', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        # request.data['space'] = unidecode(request.data.get('space'))
        request.data['max_capacity'] = self._get_capacity_by_type(request.data.get('splitter_type'))
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'Splitter', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        errors = instance.can_delete()
        if errors:
            return Response(dict(result=dict(errors=errors)), status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        Splitter.soft_delete(instance)
        description = f"Delete splitter ID={instance.id}"
        add_audit_log(request, 'Splitter', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        if Splitter.objects.filter(FAT__id=self.request.data.get('FAT'),
                                   patch_panel_port__id=self.request.data.get('patch_panel_port')).\
                                   exclude(deleted_at__isnull=False):
            raise ValidationError(dict(results="The selected patch panel port number has been already used."))
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()

    def perform_update(self, serializer):
        instance = self.get_object()
        if Splitter.objects.filter(FAT__id=self.request.data.get('FAT'),
                                   patch_panel_port__id=self.request.data.get('patch_panel_port')).\
                                   exclude(deleted_at__isnull=False).exclude(pk=instance.pk):
            raise ValidationError(dict(results="The selected patch panel port number has been already used."))
        serializer.save()

    @action(detail=False, methods=["get"])
    def ports(self, request, pk=None):
        try:
            splitter_obj = Splitter.objects.get(id=pk)
            available_ports = splitter_available_ports(splitter_obj)
            if len(available_ports) == 0:
                return JsonResponse({'results': "There are no available ports in this splitter."},
                                    status=status.HTTP_204_NO_CONTENT)
            return JsonResponse({'results': available_ports}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

    @action(detail=True, methods=["get"])
    def legs(self, request, pk=None):
        try:
            splitter_obj = Splitter.objects.get(id=pk)
            legs_count = splitter_obj.splitter_type.legs_count
            pp_ports = TerminalPort.objects.filter(in_splitter=splitter_obj).exclude(deleted_at__isnull=False)
            legs_info = []
            for i in range(1, legs_count + 1):
                leg_info = {
                            "leg_number": i,
                            "pp_port_info": {
                                "id": None,
                                "terminal": None,
                                "code": None,
                                "cassette_number": None,
                                "port_number": None,
                                "cassette_port": None
                            }
                        }
                for port in pp_ports:
                    if i == port.splitter_leg_number:
                       leg_info = {
                            "leg_number": i,
                            "pp_port_info": {
                                "id": port.id,
                                "terminal": port.terminal_id,
                                "code": port.terminal.code,
                                "cassette_number": port.cassette_number,
                                "port_number": port.port_number,
                                "cassette_port": f"{port.cassette_number}-{port.port_number}"
                            }
                        }
                legs_info.append(leg_info)
            return JsonResponse({'results': legs_info}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})


class OntViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = OntSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('ont', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        ontType = unidecode(request.data.get('ont_type')).strip()
        ontTypeText = unidecode(request.data.get('ont_type_text')).strip()
        if ontType is None or ontType == '' and ontTypeText != '':
            ontTypeInstance, created = ONTType.objects.get_or_create(name=ontTypeText)
            ontType = ontTypeInstance.id

        request.data['ont_type'] = ontType
        request.data['serial_number'] = unidecode(request.data.get('serial_number')).strip()
        request.data['mac_address'] = unidecode(request.data.get('mac_address')).strip()
        request.data['profile'] = unidecode(request.data.get('profile'))
        request.data['olt_slot_number'] = int(unidecode(str(request.data.get('olt_slot_number'))))
        request.data['olt_port_number'] = int(unidecode(str(request.data.get('olt_port_number'))))
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add ONT ID={serializer.data['id']}"
        add_audit_log(request, 'ONT', serializer.data['id'], 'Create', description)
        return Response(dict(result=serializer.data, status=status.HTTP_201_CREATED), status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['serial_number'] = unidecode(request.data.get('serial_number')).strip()
        request.data['mac_address'] = unidecode(request.data.get('mac_address')).strip()
        request.data['profile'] = unidecode(request.data.get('profile'))
        request.data['olt_slot_number'] = int(unidecode(str(request.data.get('olt_slot_number'))))
        request.data['olt_port_number'] = int(unidecode(str(request.data.get('olt_port_number'))))
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'ONT', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        ONT.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete ONT ID={instance.id}"
        add_audit_log(request, 'ONT', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        available_fat_capacity = CheckCapacityService.get_device_available_capacity('splitter',
            serializer.validated_data['splitter'].id).get('available_capacity')
        if available_fat_capacity <= 0:
            raise ValidationError(dict(results="There isn't free capacity for the selected splitter!!"))
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()


class OLTUserViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('user', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        request_from_map = self.request.query_params.get('request_from_map', None)
        if request_from_map:
            page_size = 1000 #len(queryset)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        request.data['postal_code'] = unidecode(request.data.get('postal_code'))
        request.data['fiber_number_color'] = unidecode(request.data.get('fiber_number_color'))
        #request.data['crm_id'] = int(unidecode(str(request.data.get('crm_id'))))
        request.data['cable_meterage'] = float(unidecode(str(request.data.get('cable_meterage'))))
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add user ID={serializer.data['id']}"
        add_audit_log(request, 'User', serializer.data['id'], 'Create', description)
        return Response(dict(result=serializer.data, status=status.HTTP_201_CREATED), status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        request.data['postal_code'] = unidecode(request.data.get('postal_code'))
        request.data['fiber_number_color'] = unidecode(request.data.get('fiber_number_color'))
        request.data['crm_id'] = int(unidecode(str(request.data.get('crm_id'))))
        request.data['cable_meterage'] = float(unidecode(str(request.data.get('cable_meterage'))))
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'User', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        User.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete user ID={instance.id}"
        add_audit_log(request, 'User', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()


class FatTypeViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = FATTypeSerializer

    def get_queryset(self):
        queryset = FATType.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add FAT type ID={serializer.data['id']}"
        add_audit_log(request, 'FatType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'FatType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete FAT type ID={instance_id}"
        add_audit_log(request, 'FatType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SplitterTypeViewSet(viewsets.GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin
                          ):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = SplitterTypeSerializer

    def get_queryset(self):
        queryset = SplitterType.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        request.data['legs_count'] = unidecode(request.data.get('legs_count')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add splitter type ID={serializer.data['id']}"
        add_audit_log(request, 'SplitterType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        request.data['legs_count'] = unidecode(request.data.get('legs_count')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'SplitterType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete splitter type ID={instance_id}"
        add_audit_log(request, 'SplitterType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OntTypeViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin
                     ):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = OntTypeSerializer

    def get_queryset(self):
        queryset = ONTType.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        request.data['fast_port_count'] = unidecode(request.data.get('fast_port_count')).strip()
        request.data['gig_port_count'] = unidecode(request.data.get('gig_port_count')).strip()
        request.data['band_count'] = unidecode(request.data.get('band_count')).strip()
        request.data['antenna_count'] = unidecode(request.data.get('antenna_count')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add ONT type ID={serializer.data['id']}"
        add_audit_log(request, 'OntType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        request.data['fast_port_count'] = unidecode(request.data.get('fast_port_count')).strip()
        request.data['gig_port_count'] = unidecode(request.data.get('gig_port_count')).strip()
        request.data['band_count'] = unidecode(request.data.get('band_count')).strip()
        request.data['antenna_count'] = unidecode(request.data.get('antenna_count')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'OntType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete ONT type ID={instance_id}"
        add_audit_log(request, 'OntType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MicroductTypeViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin
                           ):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = MicroductTypeSerializer

    def get_queryset(self):
        queryset = MicroductType.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        title = self.request.query_params.get('title', None)

        if title:
            queryset = queryset.filter(title__icontains=title)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add microduct type ID={serializer.data['id']}"
        add_audit_log(request, 'MicroductType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'MicroductType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete Microduct type ID={instance_id}"
        add_audit_log(request, 'MicroductType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AtbTypeViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin
                     ):

    permission_classes = (IsAuthenticated,)
    serializer_class = ATBTypeSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = ATBType.objects.all()

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add ATB type ID={serializer.data['id']}"
        add_audit_log(request, 'AtbType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['model'] = unidecode(request.data.get('model')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'AtbType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete ATB type ID={instance_id}"
        add_audit_log(request, 'AtbType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CableTypeViewSet(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin
                       ):

    permission_classes = (IsAuthenticated,)
    serializer_class = CableTypeSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 100:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = CableType.objects.all()

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['serial'] = unidecode(request.data.get('serial')).strip()
        request.data['core_count'] = unidecode(request.data.get('core_count')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add cable type ID={serializer.data['id']}"
        add_audit_log(request, 'CableType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['serial'] = unidecode(request.data.get('serial')).strip()
        request.data['core_count'] = unidecode(request.data.get('core_count')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'CableType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete cable type ID={instance_id}"
        add_audit_log(request, 'CableType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OLTTypeViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewOltTypeList)
    serializer_class = OLTTypeSerializer

    def get_queryset(self):
        queryset = OLTType.objects.all()

        return queryset

    def create(self, request, *args, **kwargs):
        name = unidecode(request.data.get('model')).strip().upper()
        model = "olt_" + unidecode(request.data.get('name')).strip().lower()
        request.data['name'] = name
        request.data['model'] = model
        request.data['card_count'] = unidecode(request.data.get('card_count')).strip()
        request.data['card_type'] = unidecode(request.data.get('card_type')).strip()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add OLT type ID={serializer.data['id']}"
        add_audit_log(request, 'OLTType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        name = unidecode(request.data.get('model')).strip().upper()
        model = "olt_" + unidecode(request.data.get('name')).strip().lower()
        request.data['name'] = name
        request.data['model'] = model
        request.data['card_count'] = unidecode(request.data.get('card_count')).strip()
        request.data['card_type'] = unidecode(request.data.get('card_type')).strip()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'OLTType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete olt type ID={instance_id}"
        add_audit_log(request, 'OLTType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HandholeViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = HandholeSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.basename == 'T':
            self.object_type = 'T'
            self.is_t = True
        else:
            self.object_type = 'handhole'
            self.is_t =False

    def get_queryset(self):
        queryset = QuerysetFactory.make('handhole', self.request)
        if self.is_t:
            queryset = queryset.filter(is_t=True)

        page_size = self.request.query_params.get('page_size', 10)
        request_from_map = self.request.query_params.get('request_from_map', None)

        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10

        if request_from_map:
            self.serializer_class = HandholeMapSerializer
            page_size = 1000 #len(queryset)

        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['is_t'] = self.is_t
        request.data['number'] = unidecode(request.data.get('number')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        if Handhole.objects.filter(number=request.data['number'], city__id=request.data['city'],
                                   urban_district=request.data.get('urban_district'), is_t=self.is_t).exclude(deleted_at__isnull=False):
            return Response(dict(results=f"The {self.object_type} with the number you have entered already exists in this city. "
                                         "Please change the number or city"), status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_current_user(request.user)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add {self.object_type} ID={serializer.data['id']}"
        add_audit_log(request, {self.object_type}, serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['is_t'] = self.is_t
        request.data['number'] = unidecode(request.data.get('number')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        if Handhole.objects.filter(number=request.data['number'], city__id=request.data['city'],
                                   urban_district=request.data.get('urban_district'), is_t=self.is_t).exclude(deleted_at__isnull=False).exclude(id=kwargs['pk']):
            return Response(dict(results=f"The {self.object_type} with the number you have entered already exists in this city. "
                                         "Please change the number or city"), status=status.HTTP_400_BAD_REQUEST)
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, {self.object_type}, serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.delete_validator(instance)
        Handhole.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete {self.object_type} ID={instance.id}"
        add_audit_log(request, {self.object_type}, instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete_validator(self, instance):
        having_cable = (
            Cable.objects.filter(
                Q(src_device_type=self.object_type, src_device_id=instance.id) |
                Q(dst_device_type=self.object_type, dst_device_id=instance.id)
            ).exclude(deleted_at__isnull=False).exists()
        )

        having_joint = instance.joint_set.all()

        having_microduct = (
            Microduct.objects.filter(
                Q(src_device_type=self.object_type, src_device_id=instance.id) |
                Q(dst_device_type=self.object_type, dst_device_id=instance.id)
            ).exclude(deleted_at__isnull=False).exists()
        )

        if having_cable:
            raise ValidationError(dict(results=_("Deletion failed. "
                                                 "It has associated cables that must be addressed before you can proceed. "
                                                 "Please delete these cables first.")))
        if having_microduct:
            raise ValidationError(dict(results=_("Deletion failed. "
                                                 "It has associated microducts that must be addressed before you can proceed. "
                                                 "Please delete these microducts first.")))

        if having_joint:
            raise ValidationError(dict(results=_("Deletion failed. "
                                                 "It has associated joints that must be addressed before you can proceed. "
                                                 "Please delete these joints first.")))



    def perform_create(self, serializer):
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()

    @action(detail=True, methods=["get"])
    def cables(self, request, pk=None):
        try:
            instance = self.get_object()
            input_cables = Cable.objects.filter(dst_device_type={self.object_type}, dst_device_id=instance.id).exclude(deleted_at__isnull=False)
            output_cables = Cable.objects.filter(src_device_type={self.object_type}, src_device_id=instance.id).exclude(deleted_at__isnull=False)

            input_cables = CableSerializer(input_cables, many=True).data
            output_cables = CableSerializer(output_cables, many=True).data
            return JsonResponse({'results': dict(input_cables=input_cables, output_cables=output_cables)},
                                status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})


class HandholeTypeViewSet(viewsets.GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = HandholeTypeSerializer

    def get_queryset(self):
        queryset = HandholeType.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add handhole type ID={serializer.data['id']}"
        add_audit_log(request, 'HandholeType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'HandholeType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete handhole ID={instance_id}"
        add_audit_log(request, 'HandholeType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OdcTypeViewSet(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin
                     ):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = CabinetTypeSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = OLTCabinetType.objects.filter(is_odc=True)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add odc type ID={serializer.data['id']}"
        add_audit_log(request, 'OdcType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'OdcType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete Odc type ID={instance_id}"
        add_audit_log(request, 'OdcType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class JointViewSet(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = JointSerializer

    def get_queryset(self):
        queryset = Joint.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        handhole_id = self.request.query_params.get('handhole_id', None)
        if handhole_id:
            queryset = queryset.filter(handhole__id=handhole_id)

        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add joint ID={serializer.data['id']}"
        add_audit_log(request, 'Joint', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'Joint', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        Joint.soft_delete(instance)
        # self.perform_destroy(instance)
        description = f"Delete joint ID={instance_id}"
        add_audit_log(request, 'Joint', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()


class JointTypeViewSet(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = JointTypeSerializer

    def get_queryset(self):
        queryset = JointType.objects.all()
        page_size = self.request.query_params.get('page_size', 10)

        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add joint type ID={serializer.data['id']}"
        add_audit_log(request, 'JointType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'Joint', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete joint type ID={instance_id}"
        add_audit_log(request, 'JointType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class HandholeRelationViewSet(viewsets.GenericViewSet,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = HandholeRelationSerializer

    def get_queryset(self):
        queryset = HandholeRelations.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        handhole_id = self.request.query_params.get('handhole_id', None)
        if handhole_id:
            queryset = queryset.filter(handhole__id=handhole_id)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_exist = self.check_instance_exists(request.data.get('relation_src_id'),
                                              request.data.get('relation_src_type'),)
        if is_exist:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            description = f"Add handhole relation ID={serializer.data['id']}"
            add_audit_log(request, 'HandholeRelation', serializer.data['id'], 'Create', description)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(dict(results=f"Please enter correct {request.data.get('relation_src_type')} id."),
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        is_exist = self.check_instance_exists(request.data.get('relation_src_id'),
                                              request.data.get('relation_src_type'), )
        if is_exist:
            self.perform_update(serializer)
            description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
            add_audit_log(request, 'HandholeRelation', serializer.data['id'], 'Update', description)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(dict(results=f"Please enter correct {request.data.get('relation_src_type')} id."),
                            status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        # instance.deleted_at = datetime.now()
        # instance.save()
        self.perform_destroy(instance)
        description = f"Delete handhole relation ID={instance_id}"
        add_audit_log(request, 'HandholeRelation', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def check_instance_exists(self, id_value, model_name):
        if model_name.lower() in ['cabinet', 'odc']:
            model_name = OLTCabinet
        elif model_name.lower() in ['fat', 'ffat', 'otb', 'tb']:
            model_name = FAT
        elif model_name.lower() in ['handhole', 't']:
            model_name = Handhole
        else:
            return False
        instance_exists = model_name.objects.filter(id=id_value).exclude(deleted_at__isnull=False).exists()
        return instance_exists


class GetDeviceCapacityAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request):
        try:
            device_type = request.GET.get('device_type', None)
            device_id = request.GET.get('device_id', None)
            device_capacity = CheckCapacityService.get_device_available_capacity(device_type, device_id)
            return JsonResponse({'results': device_capacity}, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})


class FindPointsWithRadiusAPIView(views.APIView):

    ERROR_ALL = 100
    NO_ERROR = 10

    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request):
        try:
            object_type = request.query_params.get('object_type', 'fat')
            lat = standard_lat(unidecode(request.query_params.get('lat', None))).strip()
            long = standard_long(unidecode(request.query_params.get('long', None))).strip()
            radius = unidecode(request.query_params.get('radius', None)).strip()
            if object_type != 'None' and lat != 'None' and long != 'None' and radius != 'None':
                queryset = NearestLocation.get_nearest_device(object_type, lat, long, radius)
                print(queryset)
                feasibility_status = 'Yes' if queryset else 'No'
                code = self.NO_ERROR if queryset else self.ERROR_ALL
                # first_port = 'There are no ports currently accessible or free to use.'
                # for fat in queryset:
                #     first_port = get_first_port_from_fat(fat.get('id'))
                #     if type(first_port) == dict:
                #         feasibility_status = 'Yes'
                #         code = self.NO_ERROR
                #         break
                return JsonResponse({'results': dict(feasibility_status=feasibility_status, code=code,
                                                     fat_list=queryset)}, status=status.HTTP_200_OK)
            else:
                raise ValidationError(dict(results="Please enter correct parameters!!"))

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})


class OntSetupViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.RetrieveModelMixin,
                      SetupOntMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = OntSetupSerializer
    #pagination_class = None

    def get_queryset(self):
        queryset = OntSetup.objects.all()
        #queryset = queryset.filter(updated_at=None)
        searchText = self.request.query_params.get('search_text', None)
        fat_id = self.request.query_params.get('fat_id', None)
        olt_id = self.request.query_params.get('olt_id', None)
        if searchText:
            queryset = queryset.filter(pon_serial_number__contains=searchText)

        if fat_id:
            queryset = queryset.filter(fat__id=fat_id)

        if olt_id:
            olt_obj = OLT.objects.get(id=olt_id)
            fat_list = olt_obj.fat_set.all().exclude(deleted_at__isnull=False).exclude(is_active=False)
            queryset = queryset.filter(fat__in=fat_list)

        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        return queryset.order_by('-id')

    def create(self, request, *args, **kwargs):
        request.data['confirmor'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add ONT SETUP ID={serializer.data['id']}"
        add_audit_log(request, 'OntSetup', serializer.data['id'], 'Create', description)
        ReservedPorts.setAllocated(request.data['reserved_port']);
        return Response(dict(result=serializer.data, status=status.HTTP_201_CREATED), status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=["post"], url_path='setup-by-reservation')
    def setup_by_reservation(self, request):
        reservedPortId = request.data.get('reservation_id')
        return self.config_ont_by_reservation(reservedPortId, request)


class MicroductViewSet(viewsets.GenericViewSet,
                       mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = MicroductSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('microduct', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        if not self.request.user.type_contains([FTTH_ADMIN, FTTH_OPERATOR]) and (int(page_size) < 1 or int(page_size) > 30):
            page_size = 10

        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def list(self, request, *args, **kwargs):
        map_param = self.request.query_params.get('map', None)
        if map_param:
            params = dict(province_id=request.query_params.get('province_id', None))
            objects = NearestEquipmentsFactory.create_equipment('microduct_map')(params).get_nearest()
            return JsonResponse({'results': objects}, safe=False)
        else:
            return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        src_is_exist = self.check_instance_exists(request.data.get('src_device_id'),
                                                  request.data.get('src_device_type'), )
        dst_is_exist = self.check_instance_exists(request.data.get('dst_device_id'),
                                                  request.data.get('dst_device_type'), )
        if src_is_exist and dst_is_exist:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            description = f"Add Microduct  ID={serializer.data['id']}"
            add_audit_log(request, 'Microduct', serializer.data['id'], 'Create', description)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            if not src_is_exist:
                return Response(dict(results=f"Please enter correct {request.data.get('src_device_type')} id"
                                             f" for source device."),
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(dict(results=f"Please enter correct {request.data.get('dst_device_type')} id"
                                             f" for destination device."),
                                status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        src_is_exist = self.check_instance_exists(request.data.get('src_device_id'),
                                                  request.data.get('src_device_type'), )
        dst_is_exist = self.check_instance_exists(request.data.get('dst_device_id'),
                                                  request.data.get('dst_device_type'), )
        if src_is_exist and dst_is_exist:
            self.perform_update(serializer)
            description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
            add_audit_log(request, 'Microduct', serializer.data['id'], 'Update', description)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            if not src_is_exist:
                return Response(dict(results=f"Please enter correct {request.data.get('src_device_type')} id"
                                             f" for source device."),
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(dict(results=f"Please enter correct {request.data.get('dst_device_type')} id"
                                             f" for destination device."),
                                status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        description = f"Delete  Microduct ID={instance.id}"
        add_audit_log(request, ' Microduct', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()

    def check_instance_exists(self, id_value, model_name):
        if model_name.lower() == 'cabinet':
            model_name = OLTCabinet
        elif model_name.lower() in ['fat', 'ffat', 'otb', 'tb']:
            model_name = FAT
        elif model_name.lower() in ['handhole', 't']:
            model_name = Handhole
        else:
            return False
        instance_exists = model_name.objects.filter(id=id_value).exists()
        return instance_exists


class CableViewSet(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewCableList)
    serializer_class = CableSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('cable', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        map = self.request.query_params.get('map', None)
        if map:
            self.serializer_class = CableMapSerializer
        if not self.request.user.type_contains([FTTH_ADMIN, FTTH_OPERATOR]) and (int(page_size) < 1 or int(page_size) > 30):
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add  Cable ID={serializer.data['id']}"
        add_audit_log(request, ' Cable', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        self.check_is_valid()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, ' Cable', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Cable.objects.filter(uplink=instance, deleted_at__isnull=True).count():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        instance.soft_delete()
        # self.perform_destroy(instance)
        description = f"Delete  Cable ID={instance.id}"
        add_audit_log(request, ' Cable', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        obj = serializer.save()
        obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                               object_id=obj.id,
                                               creator=self.request.user)
        obj.property = obj_property
        obj.save()

    def filter(self, queryset):
        usage_set = ['microfiber']
        queryset = queryset.exclude(usage__in=usage_set)
        return queryset

    def check_is_valid(self):
        instance = self.get_object()
        uplink = self.request.data.get('uplink')
        if uplink and instance.id == uplink:
            raise ValidationError(dict(results="You will not be able to select a cable as its own uplink."))


class TerminalViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = TerminalSerializer
    model_mapping = {
        'fat': FAT,
        'cabinet': OLTCabinet,
        'joint': Joint,
        'odc': OLTCabinet,
    }

    def get_model(self, content_type_name):
        return self.model_mapping.get(content_type_name.lower())

    def get_instance(self, model, object_id):
        try:
            return model.objects.get(pk=object_id)
        except ObjectDoesNotExist:
            return None

    def get_queryset(self):
        queryset = Terminal.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        code = self.request.query_params.get('code', None)
        object_type = self.request.query_params.get('content_type', None)
        object_id = self.request.query_params.get('content_id', None)

        if code:
            queryset = queryset.filter(code__icontains=code)

        if object_type:
            model = self.get_model(object_type)
            if not model:
                raise ValidationError(dict(results='Invalid content_type'))
            queryset = queryset.filter(content_type=ContentType.objects.get_for_model(model))

        if object_id:
            queryset = queryset.filter(object_id=object_id)

        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10

        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        content_type_name = request.data.get('object_type')
        model = self.get_model(content_type_name)
        if not model:
            return Response({'results': 'Invalid object_type'}, status=status.HTTP_400_BAD_REQUEST)
        object_id = request.data.get('object_id')
        instance = self.get_instance(model, object_id)
        if not instance:
            return Response({'results': 'Object with specified object_id does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        content_type = ContentType.objects.get_for_model(instance)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['content_type'] = content_type
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add  Terminal ID={serializer.data['id']}"
        add_audit_log(request, ' Terminal', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        content_type_name = request.data.get('object_type')
        model = self.get_model(content_type_name)
        if not model:
            return Response({'results': 'Invalid object_type'}, status=status.HTTP_400_BAD_REQUEST)
        object_id = request.data.get('object_id')
        instance = self.get_instance(model, object_id)
        if not instance:
            return Response({'results': 'Object with specified object_id does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)

        content_type = ContentType.objects.get_for_model(instance)
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['content_type'] = content_type
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, ' Terminal', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        description = f"Delete  Terminal ID={instance.id}"
        add_audit_log(request, ' Terminal', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        cassette_count = serializer.validated_data.get('cassette_count')
        port_count = serializer.validated_data.get('port_count')
        if cassette_count is None or port_count is None:
            raise ValidationError(dict(results='Both cassette_count and port_count must be provided and be greater than 0.'))

        if not isinstance(cassette_count, int) or not isinstance(port_count,
                                                                 int) or cassette_count < 1 or port_count < 1:
            raise ValidationError(dict(results='Both cassette_count and port_count must be positive integers.'))
        with transaction.atomic():
            obj = serializer.save()
            obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                                   object_id=obj.id,
                                                   creator=self.request.user)
            obj.property = obj_property
            obj.save()
            terminal_ports = [
                TerminalPort(port_number=port, cassette_number=cassette, terminal=obj)
                for cassette in range(1, cassette_count + 1)
                for port in range(1, port_count + 1)
            ]
            TerminalPort.objects.bulk_create(terminal_ports)

    def perform_update(self, serializer):
        cassette_count = serializer.validated_data.get('cassette_count')
        port_count = serializer.validated_data.get('port_count')
        if cassette_count is None or port_count is None:
            raise ValidationError(
                dict(results='Both cassette_count and port_count must be provided and be greater than 0.'))

        if not isinstance(cassette_count, int) or not isinstance(port_count,
                                                                 int) or cassette_count < 1 or port_count < 1:
            raise ValidationError(dict(results='Both cassette_count and port_count must be positive integers.'))

        with transaction.atomic():
            terminal_id = self.kwargs.get('pk')
            delete_terminal_ports = TerminalPort.objects.filter(terminal__id=terminal_id).delete()
            terminal = serializer.save()
            terminal_ports = [
                TerminalPort(port_number=port, cassette_number=cassette, terminal=terminal)
                for cassette in range(1, cassette_count + 1)
                for port in range(1, port_count + 1)
            ]
            TerminalPort.objects.bulk_create(terminal_ports)


class TerminalPortViewSet(viewsets.GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = TerminalPortSerializer

    def get_queryset(self):
        queryset = TerminalPort.objects.all()
        cable_id = self.request.query_params.get('cable_id', None)
        cassette_port = self.request.query_params.get('cassette_port', None)
        page_size = self.request.query_params.get('page_size', None)
        all = self.request.query_params.get('all', 'True')
        available_ports = self.request.query_params.get('available_ports', None)
        if page_size:
            if int(page_size) < 1 or int(page_size) > 30:
                page_size = 10
        if cable_id:
            queryset = queryset.filter(cable_id=cable_id)

        if cassette_port:
            separator = '_' if '_' in cassette_port else '-'
            parts = cassette_port.split(separator)
            cassette_number = parts[0] if len(parts) > 0 else ''
            port_number = parts[1] if len(parts) > 1 else ''
            if cassette_number.isdigit() and port_number.isdigit():
                queryset = queryset.filter(cassette_number=cassette_number, port_number=port_number)
            elif cassette_number.isdigit() and port_number is '':
                queryset = queryset.filter(cassette_number=cassette_number)
            elif cassette_number == '' and port_number.isdigit():
                queryset = queryset.filter(port_number=port_number)
            else:
                queryset = queryset.none()

        terminal = Terminal.objects.get(id=self.kwargs.get('terminal_pk'))
        queryset = queryset.filter(terminal=terminal.id)

        if available_ports:
            terminal_id = self.kwargs.get('terminal_pk')
            if terminal_id:
                used_ports = TerminalPort.objects.filter(Q(splitter__patch_panel_port__terminal__id=terminal_id,
                                                         splitter__deleted_at__isnull=True) |
                                                         Q(reservedports__patch_panel_port__terminal__id=terminal_id, reservedports__status__in=ReservedPorts.NOT_FREE_STATUZ) |
                                                         Q(fat__patch_panel_port__terminal__id=terminal_id, fat__deleted_at__isnull=True))
                queryset = queryset.exclude(id__in=used_ports.values('id'))
        if not page_size:
            page_size = len(queryset)
        pagination.PageNumberPagination.page_size = page_size
        return queryset.exclude(deleted_at__isnull=False).order_by('id')

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add  TerminalPort ID={serializer.data['id']}"
        add_audit_log(request, ' TerminalPort', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.is_used(instance.port_number, instance.terminal.id)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, ' TerminalPort', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.is_used(instance.port_number, instance.terminal.id)
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        description = f"Delete  Terminal ID={instance.id}"
        add_audit_log(request, ' TerminalPort', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        terminal = serializer.validated_data['terminal']
        port_number = serializer.validated_data['port_number']
        cassette_number = serializer.validated_data['cassette_number']
        if TerminalPort.objects.filter(port_number=port_number, terminal=terminal, cassette_number=cassette_number).exists():
            raise ValidationError(dict(results=f"Cassette {cassette_number}/ port {port_number} has been already used. "
                                               f"Please use another port or cassette."))
        serializer.save()

    def perform_update(self, serializer):
        terminal = serializer.validated_data['terminal']
        port_number = serializer.validated_data['port_number']
        cassette_number = serializer.validated_data['cassette_number']
        obj_is_exists = TerminalPort.objects.filter(port_number=port_number, terminal=terminal, cassette_number=cassette_number).exclude(
                        id=serializer.instance.pk).exists()
        if obj_is_exists:
            raise ValidationError(dict(results=f"Cassette {cassette_number}/ port {port_number} has been already used. "
                                               f"Please use another port or cassette."))
        serializer.save()

    def is_used(self, port_number, terminal_id):
        fat_obj = FAT.objects.filter(patch_panel_port=port_number, terminal__id=terminal_id).exclude(
            deleted_at__isnull=False).exclude(is_active=False).first()
        if fat_obj:
            raise ValidationError(dict(results=f"The pach panel port has been already used in fat ({fat_obj.name}) "
                                               f"so you can't edit or delete it."))

    @action(detail=False, methods=["post"])
    def saveall(self, request, *args, **kwargs):
        ports = self.request.data['ports']
        for port in ports:
            terminalPort = TerminalPort.objects.get(cassette_number=port['cassette_number'],
                                                    port_number=port['port_number'],
                                                    terminal__id=port['terminal'])
            terminalPort.cable = Cable.objects.get(id=port['cable'])
            terminalPort.loose_color = port['loose_color']
            terminalPort.core_color = port['core_color']
            terminalPort.save()
            description = f"Add  TerminalPort ID={terminalPort.id}"
            add_audit_log(request, ' TerminalPort', terminalPort.id, 'Update Ports', description)
        return Response(self.request.data, status=status.HTTP_201_CREATED)


class BulkSaveTerminalPortsAPIView(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)

    def post(self, request):
        checkingPort = None
        try:
            ports = self.request.data['ports']
            for port in ports:
                terminalPort = None
                checkingPort = port
                if port.get('terminal', None) and port.get('port_number', None) and port.get('cassette_number', None):
                    terminalPort = TerminalPort.objects.get(cassette_number=port['cassette_number'],
                                                            port_number=port['port_number'],
                                                            terminal__id=port['terminal'])
                elif port.get('in_splitter') and port.get('splitter_leg_number'):
                    terminalPort = TerminalPort.objects.filter(in_splitter__id=port.get('in_splitter'),
                                                               splitter_leg_number=port.get('splitter_leg_number')).first()
                if terminalPort:
                    if port.get('cable', None):
                        terminalPort.cable = Cable.objects.get(id=port.get('cable'))
                        terminalPort.loose_color = port.get('loose_color', None)
                        terminalPort.core_color = port.get('core_color', None)
                    else:
                        terminalPort.cable = None
                        terminalPort.loose_color = None
                        terminalPort.core_color = None
                    if port.get('out_cable', None):
                        terminalPort.out_cable = Cable.objects.get(id=port.get('out_cable'))
                        terminalPort.out_loose_color = port.get('out_loose_color', None)
                        terminalPort.out_core_color = port.get('out_core_color', None)
                    else:
                        terminalPort.out_cable = None
                        terminalPort.out_loose_color = None
                        terminalPort.out_core_color = None
                    if port.get('in_splitter') and port.get('splitter_leg_number') and port.get('terminal'):
                        splitter = get_object_or_404(Splitter, pk=port.get('in_splitter'))

                        TerminalPort.objects.filter(in_splitter__id=port.get('in_splitter'),
                                                    splitter_leg_number=port.get('splitter_leg_number')).update(
                            in_splitter=None, splitter_leg_number=None
                        )
                        terminalPort.in_splitter = splitter
                        terminalPort.splitter_leg_number = port.get('splitter_leg_number')
                    else:
                        terminalPort.in_splitter = None
                        terminalPort.splitter_leg_number = None

                    olt_port_info = port.get('olt_port_info')
                    if olt_port_info:
                        olt_id = olt_port_info.get('olt')
                        card_number = olt_port_info.get('card_number')
                        port_number = olt_port_info.get('port_number')

                        if olt_id and card_number and port_number:
                            olt_port = get_object_or_404(
                                OltPort,
                                card__olt__id=olt_id,
                                card__number=card_number,
                                port_number=port_number
                            )
                            terminalPort.olt_port = olt_port
                        else:
                            terminalPort.olt_port = None
                    else:
                        terminalPort.olt_port = None
                    terminalPort.save()
                    description = f"Add  TerminalPort ID={terminalPort.id}"
                    add_audit_log(request, ' TerminalPort', terminalPort.id, 'Update Ports', description)
            return Response(self.request.data, status=status.HTTP_201_CREATED)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno), 'port': checkingPort},
                                status=status.HTTP_400_BAD_REQUEST)


class MicroductsCablesViewSet(viewsets.GenericViewSet,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = MicroductsCablesSerializer

    def get_queryset(self):
        queryset = MicroductsCables.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = page_size
        return queryset.filter(microduct=self.kwargs.get('microduct_pk'))

    def create(self, request, *args, **kwargs):
        if self.is_exist(request.data, 'create'):
            return Response(dict(results="selected loose-color is already used."
                                         " Please use another loose-color."), status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add  MicroductsCables ID={serializer.data['id']}"
        add_audit_log(request, ' MicroductCables', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        if self.is_exist(request.data, 'update'):
            return Response(dict(results="selected loose-color is already used."
                                         " Please use another loose-color."), status=status.HTTP_400_BAD_REQUEST)
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, ' MicroductCables', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        description = f"Delete  MicroductsCables ID={instance.id}"
        add_audit_log(request, ' MicroductCables', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_exist(self, data, request_type):
        loose_color = data.get('loose_color')
        microduct_id = data.get('microduct')
        if request_type == 'create':
            return MicroductsCables.objects.filter(microduct__id=microduct_id, loose_color=loose_color).\
                exclude(deleted_at__isnull=False).exists()
        pk = self.kwargs.get('pk')
        return MicroductsCables.objects.filter(~Q(id=pk), microduct__id=microduct_id, loose_color=loose_color).\
            exclude(deleted_at__isnull=False).exists()

    def perform_create(self, serializer):
        cable_id = self.request.data.get('cable', None)
        microduct_id = self.request.data.get('microduct', None)
        if MicroductsCables.objects.filter(cable__id=cable_id, microduct__id=microduct_id).exclude(deleted_at__isnull=False):
            raise ValidationError(dict(results="Entered cable and microduct have been already used."))
        serializer.save()


class JointsCablesViewSet(viewsets.GenericViewSet,
                          mixins.ListModelMixin,
                          mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = JointsCablesSerializer

    def get_queryset(self):
        queryset = JointsCables.objects.all()
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = page_size

        return queryset.filter(joint=self.kwargs.get('joint_pk'))

    def create(self, request, *args, **kwargs):
        if self.is_exist(request.data, 'create'):
            return Response(dict(results="The selected cable and loose-color are already used."
                                         " Please use another cable or loose-color."), status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add  JointsCables ID={serializer.data['id']}"
        add_audit_log(request, ' JointsCables', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        if self.is_exist(request.data, 'update'):
            return Response(dict(results="The selected cable and loose-color are already used."
                                         " Please use another cable or loose-color."), status=status.HTTP_400_BAD_REQUEST)
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, ' JointsCables', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        JointsCables.soft_delete(instance)
        # instance.deleted_at = datetime.now()
        # instance.save()
        # self.perform_destroy(instance)
        description = f"Delete  JointsCables ID={instance.id}"
        add_audit_log(request, ' JointsCables', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_exist(self, data, request_type):
        cable_id = data.get('cable')
        loose_color = data.get('loose_color')
        if request_type == 'create':
            return JointsCables.objects.filter(cable__id=cable_id, loose_color=loose_color). \
                exclude(deleted_at__isnull=False).exists()
        pk = self.kwargs.get('pk')
        return JointsCables.objects.filter(~Q(id=pk), cable__id=cable_id, loose_color=loose_color). \
            exclude(deleted_at__isnull=False).exists()


class ReservedPortsViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin,
                           SetupOntMixin):

    permission_classes = (IsAuthenticated, CanViewReservedPorts)
    serializer_class = ReservedPortSerializer

    NO_ERROR = 10
    ERROR_LEG_RESERVED = 11
    ERROR_CUSTOMER_RESERVED = 12
    ERROR_SPLITTER_NOT_FOUND = 13
    ERROR_INVALID_INPUT = 14
    ERROR_UNABLE_CHANGE_RESERVATION = 15
    ERROR_LEG_ALLOCATED = 16
    ERROR_PORT_NOT_AVAILABLE = 17
    ERROR_LEG_READY_TO_INSTALL = 18
    ERROR_SPLITTER_OR_LEG_ARE_USED = 19
    ERROR_MISSING_SPLITTER_OR_LEG = 20
    ERROR_ALL = 100

    def get_serializer_class(self):
        if self.request.user.type_contains(FTTH_WEB_SERVICE):
            return ReservedPortSerializer
        return ReservedPortFullSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('reserved_ports', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        if self.request.user.type_contains(FTTH_WEB_SERVICE):
            queryset = queryset.filter(operator__id=self.request.user.id)

        return queryset

    def checkIsValid(self):
        data = self.request.data
        if data.get('splitter', None) and data.get('leg_number', None):
            splitterExists = Splitter.objects.filter(pk=data['splitter'], is_active=True).exclude(
                deleted_at__isnull=False).exists()
            if splitterExists == False:
                return [False, _("Splitter not found"), self.ERROR_SPLITTER_NOT_FOUND]
            record = ReservedPorts.objects.filter(splitter__id=data['splitter'], leg_number=data['leg_number'])
        else:
            pp_port_exists = TerminalPort.objects.filter(pk=data['patch_panel_port']).exclude(
                deleted_at__isnull=False).exists()
            if pp_port_exists == False:
                return [False, _("Patch panel port not found."), self.ERROR_SPLITTER_NOT_FOUND]
            pp_port_used_by_splitter = Splitter.objects.filter(patch_panel_port__id=data['patch_panel_port'], deleted_at__isnull=True).first()
            if pp_port_used_by_splitter:
                return [False, _("This Patch panel port is used by splitter, id=") + str(pp_port_used_by_splitter.id), self.ERROR_LEG_RESERVED]
            record = ReservedPorts.objects.filter(patch_panel_port__id=data['patch_panel_port'])
        record = record.filter(status__in=ReservedPorts.NOT_FREE_STATUZ).first()
        if record:
            if record.status == ReservedPorts.STATUS_RESERVED:
                return [False, _("This port/leg number is reserved, id=") + str(record.id), self.ERROR_LEG_RESERVED]
            elif record.status == ReservedPorts.STATUS_ALLOCATED:
                return [False, _("This port/leg number is allocated, id=") + str(record.id), self.ERROR_LEG_ALLOCATED]
            elif record.status == ReservedPorts.STATUS_READY_TO_INSTALL:
                return [False, _("This port/leg number is ready to install, id=") + str(record.id), self.ERROR_LEG_READY_TO_INSTALL]
            return [False, _("Port/Leg number is not available") + str(record.id), self.ERROR_ALL]

        record = ReservedPorts.objects.filter(crm_username=data['crm_username'], status__in=ReservedPorts.NOT_FREE_STATUZ).first()
        if record:
            return [False, _("A port is already reserved for this customer"), self.ERROR_CUSTOMER_RESERVED]

        if bool(re.match('[0-9a-zA-Z\s]+$', data['customer_name_en'])) is False:
            return [False, _("English customer's name only accepts english characters"), self.ERROR_INVALID_INPUT]
        
        return [True, "", self.NO_ERROR]

    def create(self, request, *args, **kwargs):
        #request.data['status'] = ReservedPorts.STATUS_READY_TO_CONFIG
        isValid = self.checkIsValid()
        if isValid[0] is False:
            return Response(dict(results=isValid[1], code=isValid[2]), status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        self.addLog(serializer.data['id'], 'Create')
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        data = request.data
        splitter_id = data.get('splitter', None)
        leg_number = data.get('leg_number', None)
        if splitter_id and leg_number:
            reserved_port = ReservedPorts.objects.filter(splitter=splitter_id, leg_number=leg_number).exclude(
                status=ReservedPorts.STATUS_CANCELED).exclude(id=kwargs['pk'])
            splitter = Splitter.objects.get(id=splitter_id)
            if reserved_port:
                return Response(
                    {'results': "The selected splitter and leg number have been already used. "
                                "Please use another splitter or leg number.",
                     'code': self.ERROR_SPLITTER_OR_LEG_ARE_USED}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'results': _("Both splitter ID and leg number are required."),
                 'code': self.ERROR_MISSING_SPLITTER_OR_LEG}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        old_data = self.serializer_class(instance).data
        instance.splitter = splitter
        instance.leg_number = leg_number
        instance.save()
        serializer = self.serializer_class(instance)
        desc = dict(old=old_data, new=serializer.data)
        self.addLog(instance.id, 'Update', description=str(desc))
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        instance.operator = self.request.user
        instance.save()

    @action(detail=True, methods=["put"])
    def cancel(self, request, pk=None):
        success = False
        reserved_port = self.get_object()
        if (reserved_port and reserved_port.status in [ReservedPorts.STATUS_RESERVED, ReservedPorts.STATUS_READY_TO_CONFIG]):
            reserved_port.status = ReservedPorts.STATUS_CANCELED
            reserved_port.save()
            success = True
            self.addLog(reserved_port.id, 'Cancel')

        if success is False:
            return Response({'results': _("Unable to change reserved port"), 'code': self.ERROR_UNABLE_CHANGE_RESERVATION}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({'results': _("Reservation canceled successfully"), 'code': self.NO_ERROR}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path='setup-ont')
    def setup_ont(self, request, pk=None):
        reserved_port = self.get_object()
        #PishgamanGeteway().config_acs(reserved_port.crm_username, request.data.get('pon_serial_number'))
        if (reserved_port and reserved_port.status in [ReservedPorts.STATUS_READY_TO_CONFIG]):
            return self.config_ont_by_reservation(reserved_port.id, request)
        
        return Response({'results': _("Reservation status is not acceptable."), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path='complete-setup-info')
    def complete_setup_info(self, request, pk=None):
        reserved_port = self.get_object()
        if (reserved_port and reserved_port.status in [ReservedPorts.STATUS_READY_TO_INSTALL]):
            try:
                with transaction.atomic():
                    reserved_port.cable_type = CableType.objects.filter(pk=request.data['cable_type']).first()
                    reserved_port.cable_meterage = request.data['cable_meterage']
                    reserved_port.atb_type = ATBType.objects.filter(pk=request.data['atb_type']).first()
                    reserved_port.patch_cord_type = PatchCordType.objects.filter(pk=request.data['patch_cord_type']).first()
                    reserved_port.patch_cord_length = request.data['patch_cord_length']
                    reserved_port.fiber_number_color = request.data['fiber_number_color']
                    reserved_port.status = ReservedPorts.STATUS_ALLOCATED
                    reserved_port.save()

                    self.addLog(reserved_port.id, 'install info added')
                    return Response({'results': _("Data Saved Successfully"), 'code': self.NO_ERROR}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
        return Response({'results': _("Could not update installation info") + " {0}".format(reserved_port.status), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def ticket(self, request, pk=None):
        reservedPort = self.get_object()
        ticket = Ticketer().findInstallServiceTicket(reservedPort)
        if (ticket == None):
            return Response({'results': _("Ticket Not Found")}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'results': {'id': ticket.id, 'subject': ticket.subject}}, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"])
    def set_tech_agent(self, request, pk=None):
        user_id = self.request.data.get('tech_agent', None)
        tech_agent = get_object_or_404(MainUser, pk=user_id)
        if user_id is None or str(user_id).isnumeric() == False or tech_agent is None:
            return Response({'results': _("Technical agent not found"), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

        reservedPort = self.get_object()
        if (reservedPort.tech_agent != None and reservedPort.tech_agent.id == user_id):
            return Response({'results': _("Technical agent is already assigned "), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with (transaction.atomic()):
                oldTechnicalAgent = reservedPort.tech_agent
                reservedPort.tech_agent = tech_agent
                reservedPort.save()
                sentTicket = Ticketer().findInstallServiceTicket(reservedPort)
                if (sentTicket):
                    Ticketer().moveInstallServiceTicketToNewTechAgent(sentTicket, reservedPort, oldTechnicalAgent)
                else:
                    Ticketer().sendInstallServiceTicket(reservedPort, tech_agent)
                CreateReminders().Reserved_port_notification(reservedPort, tech_agent, 'tech_agent')
                return Response({'results': _("New tech agent successfully asigned to reserved port"), 'code': self.NO_ERROR}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)

        return Response({'results': _("Could not update installation info") + " {0}".format(reservedPort.status), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def set_installer(self, request, pk=None):
        user_id = self.request.data.get('installer', None)
        installer = get_object_or_404(MainUser, pk=user_id)
        if user_id is None or str(user_id).isnumeric() == False or installer is None:
            return Response({'results': _("Installer not found"), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

        reservedPort = self.get_object()
        if (reservedPort.installer != None and reservedPort.installer.id == user_id):
            return Response({'results': _("Installer is already assigned "), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with (transaction.atomic()):
                oldInstaller = reservedPort.installer
                reservedPort.installer = installer
                reservedPort.save()
                sentTicket = Ticketer().findInstallServiceTicket(reservedPort)
                if (sentTicket):
                    Ticketer().moveInstallServiceTicketToNewInstaller(sentTicket, reservedPort, oldInstaller)
                else:
                    Ticketer().sendInstallServiceTicket(reservedPort, installer)
                return Response({'results': _("New installer successfully asigned to reserved port"), 'code': self.NO_ERROR}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)

        return Response({'results': _("Could not update installation info") + " {0}".format(reservedPort.status), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def set_cabler(self, request, pk=None):
        user_id = self.request.data.get('cabler', None)
        cabler = get_object_or_404(MainUser, pk=user_id)
        if user_id is None or str(user_id).isnumeric() == False or cabler is None:
            return Response({'results': _("Cabler not found"), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

        reservedPort = self.get_object()
        if (reservedPort.cabler != None and reservedPort.cabler.id == user_id):
            return Response({'results': _("Cabler is already assigned "), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                oldCabler = reservedPort.cabler
                reservedPort.cabler = cabler
                reservedPort.save()
                sentTicket = Ticketer().findInstallServiceTicket(reservedPort)
                if (sentTicket):
                    Ticketer().moveInstallServiceTicketToNewCabler(sentTicket, reservedPort, oldCabler)
                else:
                    Ticketer().sendInstallServiceTicket(reservedPort, cabler)
                CreateReminders().Reserved_port_notification(reservedPort, cabler, 'cabler')
                return Response({'results': _("New cabler successfully asigned to reserved port"), 'code': self.NO_ERROR}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
        return Response({'results': _("Could not update installation info") + " {0}".format(reservedPort.status), 'code': self.ERROR_INVALID_INPUT}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=["put"])
    def ready_to_install(self, request, pk=None):
        success = False
        pon_serial_number = self.request.data.get('pon_serial_number', None)
        reserved_port = self.get_object()
        if (reserved_port and reserved_port.status in [ReservedPorts.STATUS_RESERVED]):
            if pon_serial_number:
                reserved_port.pon_serial_number = pon_serial_number
            reserved_port.status = ReservedPorts.STATUS_READY_TO_CONFIG
            reserved_port.save()
            success = True
            self.addLog(reserved_port.id, 'ready to install')

        if success is False:
            return Response({'results': _("Unable to ready to install. The port has been already reserved or allocated."),
                             'code': self.ERROR_UNABLE_CHANGE_RESERVATION}, status=status.HTTP_400_BAD_REQUEST)
        if reserved_port.installer:
            CreateReminders().Reserved_port_notification(reserved_port, reserved_port.installer, 'installer')
        return Response({'results': _("Ready for installation."), 'code': self.NO_ERROR},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def auto_reserve(self, request, *args, **kwargs):
        try:
            fat_id = self.request.data.get('fat')
            port = get_first_port_from_fat(fat_id)
            if type(port) == dict:
                self.request.data['splitter'] = port.get('splitter_id')
                self.request.data['leg_number'] = port.get('leg_number')
                isValid = self.checkIsValid()
                if isValid[0] is False:
                    return Response(dict(results=isValid[1], code=isValid[2]), status=status.HTTP_400_BAD_REQUEST)

                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                self.addLog(serializer.data['id'], 'Create')
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response(dict(results=port,
                                     code=self.ERROR_PORT_NOT_AVAILABLE), status=status.HTTP_400_BAD_REQUEST)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})

    @action(detail=False, methods=["get"])
    def report(self, request):
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        report = reservdports_reports(start_date=start_date, end_date=end_date)
        return Response(dict(results=report))

    @action(detail=True, methods=["patch"], url_path='config-acs')
    def config_acs(self, request, pk=None):
        serial_number = self.request.data.get('serial_number', None)
        reserved_port = self.get_object()
        crm_username = reserved_port.crm_username
        response = PishgamanGeteway().config_acs(crm_username, serial_number)
        status_code = response.get('Result').get('errorCode')
        if status_code == 0 or status_code == 2954:
            reserved_port.status = ReservedPorts.STATUS_READY_TO_INSTALL
            reserved_port.pon_serial_number = serial_number
            reserved_port.save()
        return Response(dict(results=response.get('Result').get('message'), code=status_code))

    def addLog(self, id, type, description=''):
        add_audit_log(self.request, 'ReservedPort', id, type, description)


class RoutesViewSet(viewsets.GenericViewSet,
                    mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = RoutesSerializer

    def get_queryset(self):
        queryset = Routes.objects.all()
        queryset = queryset.exclude(deleted_at__isnull=False).order_by('-id')
        pagination.PageNumberPagination.page_size = 2000

        return queryset

    @action(detail=False, methods=["post"])
    def saveall(self, request):
        points = self.request.data['points']
        for point in points:
            serializer = self.serializer_class(data=point)
            serializer.is_valid(raise_exception=True)
            
        Routes.objects.filter(device_type=self.request.data['device_type'], device_id=self.request.data['device_id']).delete()
        for point in points:
            serializer = self.serializer_class(data=point)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

        if self.request.data['device_type'] == 'microduct':
            microduct_id = self.request.data['device_id']
            length = get_microduct_length(microduct_id, points)
            microduct_obj = Microduct.objects.get(id=microduct_id)
            microduct_obj.length = round(length, 2)
            microduct_obj.save()
        elif self.request.data['device_type'] == 'cable':
            cable_id = self.request.data['device_id']
            length = get_cable_length(cable_id, points)
            cable_obj = Cable.objects.get(id=cable_id)
            cable_obj.length = round(length, 2)
            cable_obj.save()

        return Response(self.request.data, status=status.HTTP_201_CREATED)


class ODCViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.DestroyModelMixin):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = ODCSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('odc', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        request_from_map = self.request.query_params.get('request_from_map', None)
        if request_from_map:
            page_size = 1000 #len(queryset)
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def create(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        request.data['is_odc'] = True
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add ODC ID={serializer.data['id']}"
        add_audit_log(request, 'ODC', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['code'] = unidecode(request.data.get('code')).strip()
        request.data['lat'] = standard_lat(unidecode(request.data.get('lat')).strip())
        request.data['long'] = standard_long(unidecode(request.data.get('long')).strip())
        request.data['is_odc'] = True
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'ODC', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = datetime.now()
        instance.save()
        # self.perform_destroy(instance)
        description = f"Delete ODC ID={instance.id}"
        add_audit_log(request, 'ODC', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class PatchCordTypeTypeViewSet(viewsets.GenericViewSet,
                               mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.DestroyModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = PatchCordTypeSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 10)
        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size
        queryset = PatchCordType.objects.all()

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add patch cord type ID={serializer.data['id']}"
        add_audit_log(request, 'PatchCordType', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = serializers.serialize('json', [instance, ])
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, 'PatchCordType', serializer.data['id'], 'Update', description)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id
        self.perform_destroy(instance)
        description = f"Delete  patch cord type ID={instance_id}"
        add_audit_log(request, 'PatchCordType', instance_id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InspectionViewSet(ModelViewSet):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = InspectionSerializer
    ALLOWED_FILE_TYPES = ['.csv']
    ALLOWED_CONTENT_TYPES = [
        'text/csv',
    ]
    model_mapping = {
        'fat': FAT,
        'cabinet': OLTCabinet,
        'handhole': Handhole,
        'joint': Joint,
        'odc': OLTCabinet,
    }

    def get_model(self, content_type_name):
        return self.model_mapping.get(content_type_name.lower())

    def get_instance(self, model, object_id):
        try:
            return model.objects.get(pk=object_id, deleted_at__isnull=True)
        except ObjectDoesNotExist:
            return None

    def get_queryset(self):
        queryset = Inspection.objects.filter(deleted_at__isnull=True).order_by('-id')
        page_size = self.request.query_params.get('page_size', 10)
        content_type = self.request.query_params.get('content_type', None)
        object_id = self.request.query_params.get('object_id', None)
        status = self.request.query_params.get('status', None)

        if content_type:
            model = self.get_model(content_type)
            if not model:
                raise ValidationError(dict(results='Invalid content_type'))
            queryset = queryset.filter(content_type=ContentType.objects.get_for_model(model))

        if object_id:
            queryset = queryset.filter(object_id=object_id)
        if status:
            queryset = queryset.filter(status=status)

        if int(page_size) < 1 or int(page_size) > 30:
            page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def request_validator(self):
        content_type_name = self.request.data.get('content_type')
        model = self.get_model(content_type_name)
        if not model:
            return Response({'results': 'Invalid content_type'}, status=status.HTTP_400_BAD_REQUEST)
        object_id = self.request.data.get('object_id')
        instance = self.get_instance(model, object_id)
        if not instance:
            return Response({'results': 'Object with specified object_id does not exist'},
                            status=status.HTTP_400_BAD_REQUEST)
        content_type = ContentType.objects.get_for_model(instance).id
        self.request.data['content_type'] = content_type

    def create(self, request, *args, **kwargs):
        self.request_validator()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        description = f"Add  Inspection data={model_to_dict(instance)}"
        add_audit_log(request, ' Inspection', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        self.request_validator()
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        before_edit = model_to_dict(instance)
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        description = f"After edit: {request.data}. || \n Before edit: {before_edit}"
        add_audit_log(request, ' Inspection', serializer.data['id'], 'Update', description)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        description = f"Delete  Inspection ID={instance.id}"
        add_audit_log(request, ' Inspection', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        return serializer.save()

    @action(detail=False, methods=["post"])
    def parser(self, request):
        try:
            inspection_file = request.FILES['inspection_file']
            file_extension = os.path.splitext(inspection_file.name)[-1].lower()
            file_content_type = inspection_file.content_type

            if file_extension not in self.ALLOWED_FILE_TYPES:
                raise ValidationError("Invalid file type. Please upload a CSV file.")
            if file_content_type not in self.ALLOWED_CONTENT_TYPES:
                raise ValidationError("Invalid file content type.")

            # Read the CSV file
            decoded_file = inspection_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            results = []
            coordinates = []

            for row in reader:
                coordinates.append((row['lat'],
                                    row['lng'],
                                    row['zone'],
                                    row['cabinet'],
                                    row['handhole_number'],
                                    row['fat_atb'],
                                    row['point_shoot'],
                                    row['point_fusion'],
                                    row['initial_test'],
                                    row['cabinet_installation'],
                                    row['cabinet_power'],
                                    row['cabinet_uplink'],
                                    row['shoot_uplink'],
                                    row['serial_number'],
                                    row['site_code'],
                                    row['status'],
                                    ))

            # Query all Handholes matching the coordinates
            query = Q()
            for lat, long, _, _,  handhole_number, *_ in coordinates:
                query |= Q(long=long, lat=lat, number=handhole_number)

            handhole_objects = Handhole.objects.filter(query)

            handhole_map = {(h.lat, h.long, h.number): h.id for h in handhole_objects}

            for lat, long, zone, cabinet, handhole_number, fat_atb, point_shoot, point_fusion, initial_test, \
                    cabinet_installation, cabinet_power, cabinet_uplink, shoot_uplink, serial_number, \
                    site_code, inspection_status in coordinates:

                handhole_id = handhole_map.get((lat, long, handhole_number))
                results.append({
                    'lat': lat.strip(),
                    'lng': long.strip(),
                    'content_type': 'handhole',
                    'object_id': handhole_id,
                    'handhole_number': handhole_number.strip(),
                    'fat_atb': fat_atb.strip(),
                    'point_shoot': point_shoot.strip(),
                    'point_fusion': point_fusion.strip(),
                    'initial_test': initial_test.strip(),
                    'cabinet_installation': cabinet_installation.strip(),
                    'cabinet_power': cabinet_power.strip(),
                    'cabinet_uplink': cabinet_uplink.strip(),
                    'shoot_uplink': shoot_uplink.strip(),
                    'serial_number': serial_number.strip(),
                    'site_code': site_code.strip(),
                    'status': int(inspection_status) if inspection_status else None
                })

            return JsonResponse({'results': results}, status=status.HTTP_200_OK)

        except KeyError:
            return JsonResponse({'error': 'Missing required file parameter.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred while processing the file.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def saveall(self, request):
        inspections = self.request.data['inspections']
        results = []
        with transaction.atomic():
            for inspection in inspections:
                content_type_name = inspection.get('content_type')
                model = self.get_model(content_type_name)
                if not model:
                    continue
                inspection = self.fix_boolean_parameter(inspection)
                content_type_id = ContentType.objects.get_for_model(model).id
                inspection['content_type'] = content_type_id
                serializer = self.serializer_class(data=inspection)
                serializer.is_valid(raise_exception=True)
                instance = self.perform_create(serializer)
                description = f"Add  Inspection data={model_to_dict(instance)}"
                add_audit_log(request, ' Inspection', serializer.data['id'], 'Create', description)
                results.append(serializer.data)
        return Response(dict(results=results), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def map(self, request):
        try:
            queryset = self.get_queryset()

            categorized_lists = {
                'cabinet_list': [],
                'odc_list': [],
                'fat_list': [],
                'ffat_list': [],
                'otb_list': [],
                'tb_list': [],
                'handhole_list': []
            }

            for item in queryset:
                obj = item.content_object
                object_info = {
                    'id': obj.id,
                    'lat': obj.lat,
                    'lng': obj.long,
                    'inspection_status': item.status,
                    'inspection_status_label': item.status_label,
                    'inspection_is_passed': item.is_passed,
                    'inspection_id': item.id
                }

                if item.content_type.model == 'handhole':
                    object_info['name'] = obj.number
                    categorized_lists['handhole_list'].append(object_info)
                else:
                    object_info['name'] = obj.name

                    if item.content_type.model == 'oltcabinet':
                        if obj.is_odc:
                            categorized_lists['odc_list'].append(object_info)
                        else:
                            categorized_lists['cabinet_list'].append(object_info)
                    elif item.content_type.model == 'fat':
                        if obj.is_tb:
                            categorized_lists['tb_list'].append(object_info)
                        elif obj.is_otb:
                            categorized_lists['otb_list'].append(object_info)
                        elif obj.parent:
                            categorized_lists['ffat_list'].append(object_info)
                        else:
                            categorized_lists['fat_list'].append(object_info)

            return JsonResponse({'results': categorized_lists}, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})

    def fix_boolean_parameter(self, inspection):

        inspection['point_shoot'] = True if inspection['point_shoot'] else False
        inspection['point_fusion'] = True if inspection['point_fusion'] else False
        inspection['initial_test'] = True if inspection['initial_test'] else False
        inspection['cabinet_installation'] = True if inspection['cabinet_installation'] else False
        inspection['cabinet_power'] = True if inspection['cabinet_power'] else False
        inspection['shoot_uplink'] = True if inspection['shoot_uplink'] else False

        return inspection

class BuildingViewSet(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.RetrieveModelMixin):

    permission_classes = (IsAuthenticated, CanViewObjectsList)
    serializer_class = BuildingSerializer

    def get_queryset(self):
        queryset = QuerysetFactory.make('building', self.request)
        page_size = self.request.query_params.get('page_size', 10)
        # map = self.request.query_params.get('map', None)
        # if map:
        #     self.serializer_class = CableMapSerializer
        # if not self.request.user.type_contains([FTTH_ADMIN, FTTH_OPERATOR]) and (int(page_size) < 1 or int(page_size) > 30):
        #     page_size = 10
        pagination.PageNumberPagination.page_size = page_size

        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        description = f"Delete Building ID={instance.id}"
        add_audit_log(request, ' Building', instance.id, 'Delete', description)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)

        for bound in request.data.get("bounds", []):
            Routes.objects.create(
                index=bound['index'], 
                lat=bound['lat'],
                lng=bound['lng'],
                device_id=serializer.data['id'], 
                device_type="building"
            )

        #description = f"Add Building data={model_to_dict(instance)}"
        #add_audit_log(request, ' Building', serializer.data['id'], 'Create', description)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=self.get_success_headers(serializer.data))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        Routes.objects.filter(device_type="building", device_id=instance.id).delete()
        for bound in request.data.get("bounds", []):
            Routes.objects.create(
                index=bound['index'],
                lat=bound['lat'],
                lng=bound['lng'],
                device_id=instance.id,
                device_type="building"
            )
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def nearest(self, request):
        lat = standard_lat(unidecode(request.query_params.get('lat', None))).strip()
        lng = standard_long(unidecode(request.query_params.get('lng', None))).strip()
        radius = unidecode(request.query_params.get('radius', None)).strip()
        queryset = NearestLocation.get_nearest_building(lat, lng, radius)
        for building in queryset:
            building['bounds'] = self.get_bounds(building['id'])
        return JsonResponse({'results': queryset}, status=status.HTTP_200_OK)

    def get_bounds(self, building_id):
        items = Routes.objects.filter(device_type="building", device_id=building_id).order_by("index").all()
        bounds = []
        for item in items:
            bounds.append([item.lat, item.lng])
        return bounds


class NearestEquipmentsAPIView(views.APIView):
    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request):
        try:
            params = dict(province_id=request.query_params.get('province_id', None))
            search_text = request.query_params.get('search_text', None)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                nearest_cabinet, nearest_odc = executor.submit(NearestEquipmentsFactory.create_equipment('cabinet')(params).get_nearest).result()
                all_fat = executor.submit(NearestEquipmentsFactory.create_equipment('fat')(params).get_nearest).result()
                nearest_handhole, nearest_t = executor.submit(NearestEquipmentsFactory.create_equipment('handhole')(params).get_nearest).result()
                nearest_users = executor.submit(NearestEquipmentsFactory.create_equipment('users')(params).get_nearest).result()
            nearest_fat = all_fat.get('fat_list')
            nearest_f_fat = all_fat.get('f_fat_list')
            nearest_otb = all_fat.get('otb_list')
            nearest_tb = all_fat.get('tb_list')
            if search_text:
                nearest_cabinet = [item for item in nearest_cabinet if search_text.lower() in item["display_name"].lower()]
                nearest_fat = [item for item in nearest_fat if search_text.lower() in item["display_name"].lower()]
                nearest_handhole = [item for item in nearest_handhole if search_text.lower() in item["display_name"].lower()]

            result = dict(nearest_cabinets=nearest_cabinet, nearest_odcs=nearest_odc, nearest_fats=nearest_fat,
                          nearest_f_fats=nearest_f_fat, nearest_otbs=nearest_otb, nearest_tbs=nearest_tb,
                          nearest_handholes=nearest_handhole, nearest_t=nearest_t, nearest_users=nearest_users)
            return JsonResponse({'results': result}, status=status.HTTP_200_OK)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})


class FtthTreeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):

    serializer_class = TreeCabinetSerializer

    def get_queryset(self):
        queryset = OLTCabinet.objects.all().exclude(deleted_at__isnull=False).prefetch_related(
            Prefetch('olt_set',
                     queryset=OLT.objects.exclude(deleted_at__isnull=False).exclude(active=False).prefetch_related(
                         Prefetch('fat_set',
                                  queryset=FAT.objects.exclude(deleted_at__isnull=False).exclude(
                                      is_active=False).prefetch_related(
                                      Prefetch('splitter_set',
                                               queryset=Splitter.objects.exclude(deleted_at__isnull=False).exclude(
                                                   is_active=False).prefetch_related(
                                                   Prefetch('ont_set',
                                                            queryset=ONT.objects.exclude(
                                                                deleted_at__isnull=False).exclude(is_active=False)
                                                            )
                                               )
                                               )
                                  )
                                  )
                     )
                     )
        )
        pagination.PageNumberPagination.page_size = len(queryset)
        return queryset


class PostalCodeConversionAPIView(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)

    def get(self, request):
        try:
            postal_code = request.query_params.get('postal_code', None)
            if not postal_code:
                return JsonResponse({"results": "postal_code query parameter is required."},
                                    status=status.HTTP_400_BAD_REQUEST)
            geo_coordinate_response = convert_postal_code_to_geo_coordinate(postal_code)
            address_response = convert_postal_code_to_address(postal_code)
            if geo_coordinate_response['status'] == 200 and address_response['status'] == 200:
                response = {
                    "geo_coordinate": geo_coordinate_response['result'],
                    "address": address_response['result']
                }
                status_code = status.HTTP_200_OK
            elif geo_coordinate_response['status'] == 404 or address_response['status'] == 404:
                status_code = status.HTTP_404_NOT_FOUND
                response = 'The postal code is not available in the postal code bank'
            elif geo_coordinate_response['status'] == 408 or address_response['status'] == 408:
                status_code = status.HTTP_408_REQUEST_TIMEOUT
                response = "The request has timed out, please try again later."
            elif geo_coordinate_response['status'] == 400 or address_response['status'] == 400:
                status_code = status.HTTP_400_BAD_REQUEST
                response = "postal_code must be a 10-digit number."
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                response = "An error occurred"
            return JsonResponse({"results": response}, status=status_code)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})


class CityKMZAPIView(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)

    def get(self, request, city_id=None):
        try:
            try:
                city = City.objects.get(pk=city_id)
            except City.DoesNotExist:
                return Response(f"City with ID {city_id} does not exist", status=404)
            city_equipment_service = CityEquipmentService(city_id)
            kmz_file = city_equipment_service.export_kmz_file()
            response = Response(content_type='application/vnd.google-earth.kmz')
            response['Content-Disposition'] = f'attachment; filename="{city.name}.kmz"'
            response.content = kmz_file.getvalue()
            return response

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})

class EquipmentCreateBulk(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)

    def post(self, request):
        cabinets = request.data.get('cabinets')
        odcs = request.data.get('odcs')
        fats = request.data.get('fats')
        handholes = request.data.get('handholes')
        cables = request.data.get('cables')

        def fetchId(element):
            try:
                return int(element['object_id']), element['object_type'] + '_' + str(element['object_id'])
            except:
                return 0, 'handhole_0'
        
        def createCabinet(cabinet, isODC=False):
            cabinet['id'] = None
            cabinet['name'] = unidecode(cabinet.get('name')).strip()
            cabinet['lat'] = standard_lat(unidecode(cabinet.get('lat')).strip())
            cabinet['long'] = standard_long(unidecode(cabinet.get('long')).strip())
            cabinet['is_odc'] = isODC
            serializer = OLTCabinetSerializer(data=cabinet)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return serializer.instance

        with transaction.atomic():
            inboardCabinets = {}
            inboardOdcs = {}
            inboardFats = {}
            inboardHandholes = {}
            inboardCables = {}
            inboardOlts = {}

            for cabinet in cabinets:
                cabinetId, key = fetchId(cabinet)
                if cabinetId < 5:
                    instance = createCabinet(cabinet)
                    inboardCabinets[key] = instance
                    cabinetId = instance.id
                else:
                    selectedCabinet = OLTCabinet.objects.get(pk=cabinetId)
                    inboardCabinets[key] = selectedCabinet

                if cabinet.get('olt.name', None) and cabinetId:
                    oltData = {
                        'name' : cabinet.get('olt.name'),
                        'olt_type' : int(cabinet.get('olt.type')),
                        'fqdn' : cabinet.get('olt.fqdn'),
                        'ip' : cabinet.get('olt.ip'),
                        'capacity': 120
                    }
                    oltSerializer = OLTSerializer(data=oltData)
                    oltSerializer.is_valid(raise_exception=True)
                    oltSerializer.validated_data['cabinet'] = OLTCabinet.objects.get(pk=cabinetId)
                    oltSerializer.save()
                    inboardOlts['olt_0'] = oltSerializer.instance

            for odc in odcs:
                odcId, key = fetchId(odc)
                if odcId < 5:
                    instance = createCabinet(odc, True)
                    inboardOdcs[key] = instance
                else:
                    selectedOdc = OLTCabinet.objects.get(pk=odcId)
                    inboardOdcs[key] = selectedOdc

            for fat in fats:
                fatId, key = fetchId(fat)
                trash, oltId = fat.get('olt', 'olt_0').split("_")
                try :
                    oltId = int(oltId) if int(oltId) > 0 else inboardOlts['olt_0'].id
                except:
                    pass
                if fatId < 2:
                    fat['id'] = None
                    fat['olt'] = oltId
                    fat['name'] = unidecode(fat.get('name')).strip()
                    fat['lat'] = standard_lat(unidecode(fat.get('lat')).strip())
                    fat['long'] = standard_long(unidecode(fat.get('long')).strip())
                    fatSerializer = FATSerializer(data=fat)
                    fatSerializer.is_valid(raise_exception=True)
                    fatSerializer.validated_data['olt'] = OLT.objects.get(pk=oltId)
                    fatSerializer.save()
                    inboardFats[key] = fatSerializer.instance
                else:
                    selectedFat = FAT.objects.get(pk=fatId)
                    inboardFats[key] = selectedFat

            for handhole in handholes:
                handholeId, key = fetchId(handhole)
                if handholeId < 5:
                    handhole['id'] = None
                    handhole['number'] = unidecode(handhole.get('number')).strip()
                    handhole['lat'] = standard_lat(unidecode(handhole.get('lat')).strip())
                    handhole['long'] = standard_long(unidecode(handhole.get('long')).strip())
                    handhole['type'] = int(handhole['type'])
                    handholeSerializer = HandholeSerializer(data=handhole)
                    handholeSerializer.is_valid(raise_exception=True)
                    handholeSerializer.save()
                    inboardHandholes[key] = handholeSerializer.instance
                else:
                    selectedHandhole = Handhole.objects.get(pk=handholeId)
                    inboardHandholes[key] = selectedHandhole

            def findSrcDst(key):
                if 'cabinet' in key:
                    return inboardCabinets[key], 'cabinet'
                if 'odc' in key:
                    return inboardOdcs[key], 'odc'
                elif 'fat' in key:
                    return inboardFats[key], 'fat'
                elif 'handhole' in key:
                    return inboardHandholes[key], 'handhole'
                return None, ''


            for cable in cables:
                cableId, key = fetchId(cable)
                if cableId < 10:
                    src, srcType = findSrcDst(cable.get('src', None))
                    dst, dstType = findSrcDst(cable.get('dst', None))
                    cable['src_device_id'] = src.id
                    cable['src_device_type'] = srcType
                    cable['dst_device_id'] = dst.id
                    cable['dst_device_type'] = dstType
                    try:
                        uplink = inboardCables.get(cable.get('uplink', None))
                        cable['uplink'] = uplink.id if uplink else None
                    except:
                        pass
                    cableSerializer = CableSerializer(data=cable)
                    cableSerializer.is_valid(raise_exception=True)
                    cableSerializer.save()
                    inboardCables[key] = cableSerializer.instance
                else:
                    inboardCables[key] = Cable.objects.get(pk=cableId)

            return JsonResponse({'result': 'Board Saved Successfully', 'fat_id': (list(inboardFats.values())[-1]).id, 'status': 200})

        return JsonResponse({'result': 'Could not save board', 'status': 500})


class ApproveObjectsAPIView(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    model_mapping = {
        'building': Building,
        'cabinet': OLTCabinet,
        'odc': OLTCabinet,
        'fat': FAT,
        'ffat': FAT,
        'otb': FAT,
        'tb': FAT,
        'olt': OLT,
        'splitter': Splitter,
        'handhole': Handhole,
        't': Handhole,
        'joint': Joint,
        'patch_panel': Terminal,
        'microduct': Microduct,
        'cable': Cable
    }

    def post(self, request, *args, **kwargs):

        # Check for user permissions
        if not request.user.type_contains([FTTH_ADMIN]):
            raise ValidationError({'results': "Access Denied"})
            
        objects = request.data.get('objects')
        approver = request.user
        updated_objects = []
        errors = []

        for item in objects:
            object_type = item.get('type')
            object_id = item.get('id')

            if not object_type or not object_id:
                errors.append({'error': 'Missing type or id', 'object': item})
                continue
            model = self.model_mapping.get(object_type)

            if not model:
                errors.append({'error': f'Unknown type: {object_type}', 'object': item})
                continue
            try:
                obj = model.objects.get(id=object_id, deleted_at__isnull=True)
                if not obj.property:
                    obj_property = Property.objects.create(content_type=ContentType.objects.get_for_model(obj),
                                                           object_id=obj.id,
                                                           creator=approver,
                                                           approver=approver,
                                                           approved_at=timezone.now())
                    obj.property = obj_property
                else:
                    obj.property.approver = approver
                    obj.property.approved_at = timezone.now()
                    obj.property.save()
                if PORTMAN_ENV == 'prod' and object_type in ['fat', 'ffat']:
                    partak_status, message, partak_status_code = self.create_in_partak(obj)
                    if not partak_status and partak_status_code != 2310:
                        obj.property.approved_at = None
                        obj.property.save()
                        errors.append({'error': message, 'type': object_type, 'id': object_id})
                obj.save()
                self.mark_as_done_tickets(obj)
                updated_objects.append({'type': object_type, 'id': object_id})
            except ObjectDoesNotExist:
                errors.append({'error': 'Object not found', 'type': object_type, 'id': object_id})

        return Response({
            'updated': updated_objects,
            'errors': errors
        }, status=status.HTTP_200_OK)

    def mark_as_done_tickets(self, instance):
        Ticket.objects.filter(content_type=ContentType.objects.get_for_model(instance),
                              object_id=instance.id, type__name=TicketType.TYPE_FTTH_PLAN_CHANGES).update(done_at=datetime.now())

    def check_partak_response(self, response, payload, url):
        if response.get('ResponseStatus', {}).get('ErrorCode') != 0:
            CreateReminders.partak_api_error(response, payload, url)
            return 'Failed'
        return 'Success'

    def create_in_partak(self, instance):
        response, payload, url = PartakApi(instance).createFAT()
        response_status = self.check_partak_response(response, payload, url)
        message = response.get('ResponseStatus', {}).get('Message')
        status_code = response.get('ResponseStatus', {}).get('ErrorCode')
        if response_status == 'Failed':
            return False, _(f"Partak Error. {message}"), status_code
        return True, message, status_code


class DisapproveObjectsAPIView(views.APIView):
    permission_classes = (IsAuthenticated, CanViewObjectsList)
    model_mapping = {
        'building': Building,
        'cabinet': OLTCabinet,
        'odc': OLTCabinet,
        'fat': FAT,
        'ffat': FAT,
        'otb': FAT,
        'tb': FAT,
        'olt': OLT,
        'splitter': Splitter,
        'handhole': Handhole,
        't': Handhole,
        'joint': Joint,
        'patch_panel': Terminal,
        'microduct': Microduct,
        'cable': Cable
    }

    def post(self, request, *args, **kwargs):
        # Check for user permissions
        if not request.user.type_contains([FTTH_ADMIN]):
            raise ValidationError({'results': "Access Denied"})

        objects = request.data.get('objects')
        disapproved_objects = []
        errors = []
        for item in objects:
            object_type = item.get('type')
            object_id = item.get('id')
            reason = item.get('reason')

            if not object_type or not object_id:
                errors.append({'error': 'Missing type or id', 'object': item})
                continue
            model = self.model_mapping.get(object_type)

            if not model:
                errors.append({'error': f'Unknown type: {object_type}', 'object': item})
                continue
            try:
                obj = model.objects.get(id=object_id)
                creator = obj.property.creator if obj.property and obj.property.creator else None
                if obj.property:
                    obj.property.approved_at = None
                    obj.property.save()
                if creator:
                    Ticketer().send_disapproved_objects_ticket(obj, reason, [creator.username], request.user)
                disapproved_objects.append({'type': object_type, 'id': object_id, 'reason': reason})
            except ObjectDoesNotExist:
                errors.append({'error': 'Object not found', 'type': object_type, 'id': object_id, 'reason': reason})

        return Response({
            'disapproved': disapproved_objects,
            'errors': errors
        }, status=status.HTTP_200_OK)





def get_device_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

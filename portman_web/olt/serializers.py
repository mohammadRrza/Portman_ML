from rest_framework import serializers
from .models import *
from dslam.serializers import TelecomCenterSerializer, City, CitySerializer
from khayyam import JalaliDatetime
from .services.devices_capacity import CheckCapacityService
from users.serializers import UserUpdateSerializer
from .services.mini_services import get_olt_slot_port
import json


class OLTTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = OLTType
        fields = ('id', 'name', 'model', 'card_count', 'card_type')


class CabinetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OLTCabinetType
        fields = "__all__"


class OLTCabinetSerializer(serializers.ModelSerializer):
    city_info = CitySerializer(source="city", read_only=True, required=False)
    type_info = CabinetTypeSerializer(source="type", read_only=True, required=False)
    capacity_status = serializers.SerializerMethodField('get_capacity_status')
    display_name = serializers.SerializerMethodField('get_display_name')
    parent_info = serializers.SerializerMethodField('get_parent_info')
    code = serializers.CharField(read_only=True)
    patch_panel_count = serializers.SerializerMethodField('get_patch_panel_count')
    olt_count = serializers.SerializerMethodField('get_olt_count')
    install_manager_info = serializers.SerializerMethodField('get_install_manager_info')

    def get_parent_info(self, obj):
        if obj.parent:
            return dict(id=obj.parent.id, name=obj.parent.name, code=obj.parent.code)

    def get_display_name(self, obj):
        return obj.name

    def get_capacity_status(self, obj):
        return CheckCapacityService.get_device_available_capacity('cabinet', obj.id)

    def get_patch_panel_count(self, obj):
        return Terminal.objects.filter(content_type=ContentType.objects.get_for_model(obj), object_id=obj.id,
                                       deleted_at__isnull=True).count()

    def get_olt_count(self, obj):
        return obj.olt_set.filter(deleted_at__isnull=True).count()
    
    def get_install_manager_info(self, obj):
        user = obj.install_manager
        return dict(id=user.id, fa_first_name=user.fa_first_name, fa_last_name=user.fa_last_name) if user else None

    class Meta:
        model = OLTCabinet
        fields = "__all__"


class OLTCabinetSerializerMini(OLTCabinetSerializer):
    display_name = serializers.SerializerMethodField('get_display_name')

    def get_display_name(self, obj):
        return obj.name

    class Meta:
        model = OLTCabinet
        fields = ('id', 'name', 'code', 'type_info', 'city_info', 'urban_district', 'display_name', 'lat', 'long', 'parent_info')


class ODCSerializer(OLTCabinetSerializer):

    class Meta:
        model = OLTCabinet
        fields = ('id', 'name', 'code', 'display_name', 'type_info', 'type', 'lat', 'long', 'city', 'urban_district',
                  'city_info', 'is_odc', 'max_capacity', 'description')


class OLTSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        try:
            _request = kwargs.pop('request')
        except:
            _request = None
        super(OLTSerializer, self).__init__(*args, **kwargs)
        self.context['request'] = _request

        if remove_fields:
            for field_name in remove_fields:
                self.fields.pop(field_name)

    olt_type_info = OLTTypeSerializer(source="olt_type", read_only=True, required=False)
    cabinet_info = OLTCabinetSerializerMini(source='cabinet', read_only=True, required=False)
    text = serializers.CharField(source='name', read_only=True, required=False)
    capacity_status = serializers.SerializerMethodField('get_capacity_status')
    is_complete = serializers.SerializerMethodField('check_completeness')
    code = serializers.CharField(read_only=True)


    #vlan_number = serializers.IntegerField(read_only=True, required=False)
    #gemport = serializers.IntegerField(read_only=True, required=False)
    #intbound_index = serializers.IntegerField(read_only=True, required=False)
    #outbound_index = serializers.IntegerField(read_only=True, required=False)

    created_at = serializers.DateTimeField(
        format='%Y-%m-%d %H:%M', required=False, read_only=True)
    updated_at = serializers.DateTimeField(
        format='%Y-%m-%d %H:%M', required=False, read_only=True)
    last_sync = serializers.DateTimeField(
        format='%Y-%m-%d %H:%M:%S', required=False, read_only=True)

    total_ports_count = serializers.IntegerField(
        source='get_ports_count', read_only=True, required=False)
    up_ports_count = serializers.IntegerField(
        source='get_up_ports_count', read_only=True, required=False)
    down_ports_count = serializers.IntegerField(
        source='get_down_ports_count', read_only=True, required=False)

    sync_ports_count = serializers.IntegerField(
        source='get_sync_ports_count', read_only=True, required=False)

    nosync_ports_count = serializers.IntegerField(
        source='get_nosync_ports_count', read_only=True, required=False)

    slots = serializers.JSONField(
        source='get_slots', read_only=True, required=False)

    ports = serializers.JSONField(
        source='get_ports', read_only=True, required=False)

    dslam_availability = serializers.IntegerField(
        source='get_dslam_availability', read_only=True, required=False)

    # updated_at = serializers.SerializerMethodField('get_updated_persian_date')
    # created_at = serializers.SerializerMethodField('get_created_persian_date')
    # last_sync = serializers.SerializerMethodField('get_last_sync_persian_date')

    # def get_cabinet_info(self, obj):
    #     if obj.cabinet:
    #         return dict(id=obj.cabinet.id, code=obj.cabinet.code, x_location=obj.cabinet.x_location,
    #                     y_location=obj.cabinet.y_location,)
    #     else:
    #         return None

    def get_updated_persian_date(self, obj):
        return JalaliDatetime(obj.updated_at).strftime("%Y-%m-%d %H:%M:%S")

    def get_created_persian_date(self, obj):
        return JalaliDatetime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S")

    def get_last_sync_persian_date(self, obj):
        return JalaliDatetime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S")
    
    def get_capacity_status(self, obj):
        if (hasattr(obj, 'id')):
            return CheckCapacityService.get_device_available_capacity('olt', obj.id)
        return True

    def check_completeness(self, obj):
        if hasattr(obj, 'telnet_username') and hasattr(obj, 'set_snmp_community') and hasattr(obj, 'gemport') and \
            obj.telnet_username and obj.set_snmp_community and obj.gemport:
            return 'Yes'
        else:
            return 'No'


    class Meta:
        model = OLT
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'last_sync',
            'get_ports_count', 'get_up_ports_count', 'get_down_ports_count',
            'last_sync_duration', 'uptime', 'version', 'is_complete',
        )


class OLTSerializerMini(OLTSerializer):
    class Meta:
        model = OLT
        fields = ('id', 'name', 'code', 'ip', 'cabinet_info', 'vlan_number')


class OLTCommandSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='text', read_only=True, required=False)

    class Meta:
        model = OLTCommand
        fields = '__all__'


class TerminalSerializer(serializers.ModelSerializer):
    ports = serializers.SerializerMethodField('get_ports')
    object_type = serializers.SerializerMethodField('get_object_type')

    def get_ports(self, obj):
        ports = TerminalPort.objects.filter(terminal__id=obj.id).all()
        return TerminalPortMiniSerializer(ports, many=True).data

    def get_object_type(self, obj):
        if obj.content_type:
            return obj.content_type.model
        else:
            return None

    class Meta:
        model = Terminal
        fields = ('id', 'code', 'cassette_count', 'port_count', 'object_type', 'object_id', 'content_type', 'ports',)


class CableTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CableType
        fields = "__all__"


class RoutesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Routes
        fields = "__all__"


class CableSerializer(serializers.ModelSerializer):
    type_info = CableTypeSerializer(source='type', read_only=True, required=False)
    city_info = CitySerializer(source="city", read_only=True, required=False)
    src_device_info = serializers.SerializerMethodField('get_src_data')
    dst_device_info = serializers.SerializerMethodField('get_dst_data')
    route = serializers.SerializerMethodField('fetch_route')
    uplink_info = serializers.SerializerMethodField('get_uplink_info')
    code = serializers.SerializerMethodField()
    model_mapping = {
        'cabinet': OLTCabinet,
        'odc': OLTCabinet,
        'fat': FAT,
        'ffat': FAT,
        'otb': FAT,
        'tb': FAT,
        'handhole': Handhole,
        't': Handhole,
        'user': ReservedPorts
    }

    def fetch_route(self, obj):
        items = Routes.objects.filter(device_type="cable", device_id=obj.id).order_by("index").all()
        return RoutesSerializer(items, many=True).data

    def get_instance(self, device_type, device_id):
        try:
            model_name = self.model_mapping.get(device_type)
            if model_name:
                return model_name.objects.get(id=device_id)
        except:
            pass
        return None

    def get_src_data(self, obj):
        if obj.src_device_type == None:
            return None

        instance = self.get_instance(obj.src_device_type, obj.src_device_id)
        if instance == None:
            return None

        if obj.src_device_type.lower() == 'cabinet':
            object_info = OLTCabinetSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() in ['fat', 'ffat', 'otb', 'tb']:
            object_info = FATSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() in ['handhole', 't']:
            object_info = HandholeSerializer(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() == 'odc':
            object_info = ODCSerializer(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() == 'user':
            object_info = ReservedPortMiniSerializer(instance=instance, read_only=True, required=False).data
        else:
            object_info = None
        return object_info
    
    def get_dst_data(self, obj):
        if obj.dst_device_type is None:
            return None

        instance = self.get_instance(obj.dst_device_type, obj.dst_device_id)
        if instance == None:
            return None

        if obj.dst_device_type.lower() == 'cabinet':
            object_info = OLTCabinetSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() in ['fat', 'ffat', 'otb', 'tb']:
            object_info = FATSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() in ['handhole', 't']:
            object_info = HandholeSerializer(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() == 'odc':
            object_info = ODCSerializer(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() == 'user':
            object_info = ReservedPortMiniSerializer(instance=instance, read_only=True, required=False).data
        else:
            object_info = None
        return object_info

    def get_code(self, obj):
        return obj.code + f"[{obj.id}]"

    def get_uplink_info(self, obj):
        if obj.uplink:
            return dict(id=obj.uplink.id, code=obj.uplink.code + f"[{obj.uplink.id}]")

    class Meta:
        model = Cable
        fields = ('id', 'meterage', 'type', 'plan_code', 'uplink', 'uplink_info', 'route', 'code', 'usage', 'dst_extra_cable', 'src_extra_cable',
                  'type_info', 'length', 'dst_device_type', 'dst_device_id', 'src_device_type', 'src_device_id',
                  'src_device_info', 'dst_device_info', 'city_info',  'city')


class CableMapSerializer(CableSerializer):
    src_device_info = serializers.SerializerMethodField('get_src_data')
    dst_device_info = serializers.SerializerMethodField('get_dst_data')
    approved_at = serializers.SerializerMethodField('get_approved_at')

    def get_src_data(self, obj):
        if obj.src_device_type == None:
            return None
        instance = self.get_instance(obj.src_device_type, obj.src_device_id)
        if instance:
            return dict(id=instance.id, lat=instance.lat, long=instance.long)
        else:
            return None

    def get_dst_data(self, obj):
        if obj.dst_device_type == None:
            return None
        instance = self.get_instance(obj.dst_device_type, obj.dst_device_id)
        if instance:
            return dict(id=instance.id, lat=instance.lat, long=instance.long)
        else:
            return None

    def get_approved_at(self, obj):
        approved_at = obj.property.approved_at if obj.property and obj.property.approved_at else None
        return approved_at
    class Meta:
        model = Cable
        fields = ('id', 'meterage', 'type', 'code', 'plan_code', 'usage', 'approved_at', 'dst_extra_cable',
                  'src_extra_cable', 'length', 'route', 'src_device_info', 'dst_device_info')


class TerminalPortSerializer(serializers.ModelSerializer):
    terminal_info = serializers.SerializerMethodField('get_terminal_info')
    cable_info = serializers.SerializerMethodField('get_cable_info')
    out_cable_info = serializers.SerializerMethodField('get_out_cable_info')
    cassette_port = serializers.SerializerMethodField('get_cassette_port')
    splitter_name = serializers.SerializerMethodField('get_splitter_name')

    def get_cassette_port(self, obj):
        return f'{obj.cassette_number}-{obj.port_number}'

    def get_cable_info(self, obj):
        if obj.cable:
            return dict(id=obj.cable.id, code=obj.cable.code)

    def get_out_cable_info(self, obj):
        if obj.out_cable:
            return dict(id=obj.out_cable.id, code=obj.out_cable.code)

    def get_terminal_info(self, obj):
        if obj.terminal:
            return dict(id=obj.terminal.id, code=obj.terminal.code, cassette_count=obj.terminal.cassette_count,
                        port_count=obj.terminal.port_count)

    def get_splitter_name(self, obj):
        if obj.in_splitter:
            return obj.in_splitter.name

    class Meta:
        model = TerminalPort
        fields = ('id', 'port_number', 'cassette_number', 'cassette_port', 'cable', 'loose_color', 'core_color',
                  'cable_info',  'out_cable', 'out_loose_color', 'out_core_color', 'out_cable_info', 'in_splitter',
                  'splitter_name', 'splitter_leg_number', 'is_active',
                  'terminal', 'terminal_info')

class BuildingSerializer(serializers.ModelSerializer):
    bounds = serializers.SerializerMethodField('get_bounds')
    city_info = CitySerializer(source="city", read_only=True, required=False)

    def get_bounds(self, obj):
        items = Routes.objects.filter(device_type="building", device_id=obj.id).order_by("index").all()
        bounds = []
        for item in items:
            bounds.append([item.lat, item.lng])
        return bounds

    class Meta:
        model = Building
        fields = ('id', 'code', 'bounds', 'name', 'phone', 'unit_count', 'postal_code', 'postal_address', 'city_info', 'urban_district', 'city')

class SplitterParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Splitter
        fields = ('id', 'code')


class FATTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FATType
        fields = "__all__"


class FATParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAT
        fields = ('id', 'name', 'code', 'lat', 'long')


class FATSerializer(serializers.ModelSerializer):
    fat_type_info = FATTypeSerializer(source='fat_type', read_only=True, required=False)
    parent_info = FATParentSerializer(source='parent', read_only=True, required=False)
    olt_info = OLTSerializerMini(source='olt', read_only=True, required=False)
    patch_panel_port_info = TerminalPortSerializer(source='patch_panel_port', read_only=True)
    display_name = serializers.SerializerMethodField('get_display_name')
    fat_splitter_info = SplitterParentSerializer(source='fat_splitter', read_only=True, required=False)
    f_fat = serializers.SerializerMethodField('is_f_fat')
    device_type = serializers.SerializerMethodField('get_device_type')
    code = serializers.CharField(read_only=True)
    patch_panel_count = serializers.SerializerMethodField('get_patch_panel_count')
    splitter_count = serializers.SerializerMethodField('get_splitter_count')
    building_info = BuildingSerializer(source='building', read_only=True, required=False)
    install_manager_info = serializers.SerializerMethodField('get_install_manager_info')
    cabinet_install_manager_info = serializers.SerializerMethodField('get_cabinet_install_manager_info')

    def is_f_fat(self, obj):
        return True if obj.parent else False

    def get_device_type(self, obj):
        if obj.is_tb:
            return "tb"
        elif obj.is_otb:
            return "otb"
        elif obj.parent:
            return "ffat"
        return "fat"

    def get_display_name(self, obj):
        return obj.name + ' (' + obj.code + ')'

    def get_patch_panel_count(self, obj):
        return Terminal.objects.filter(content_type=ContentType.objects.get_for_model(obj), object_id=obj.id,
                                       deleted_at__isnull=True).count()

    def get_splitter_count(self, obj):
        return obj.splitter_set.filter(deleted_at__isnull=True).count()


    def get_cabinet_install_manager_info(self, obj):
        user = None
        if obj.olt and obj.olt.cabinet and obj.olt.cabinet.install_manager:
            user = obj.olt.cabinet.install_manager
        return dict(id=user.id, fa_first_name=user.fa_first_name, fa_last_name=user.fa_last_name) if user else None
    
    def get_install_manager_info(self, obj):
        user = obj.install_manager
        return dict(id=user.id, fa_first_name=user.fa_first_name, fa_last_name=user.fa_last_name) if user else None

    class Meta:
        model = FAT
        fields = "__all__"


class FATSerializerMini(FATSerializer):
    display_name = serializers.SerializerMethodField('get_display_name')
    city_info = serializers.SerializerMethodField('get_city_info')

    def get_display_name(self, obj):
        return obj.name + ' (' + obj.code + ')'

    def get_city_info(self, obj):
        try:
            if obj.olt and obj.olt.cabinet and obj.olt.cabinet.city:
                return CitySerializer(obj.olt.cabinet.city, many=False).data
        except:
            pass
        return None

    class Meta:
        model = FAT
        fields = ('id', 'code', 'name', 'urban_district', 'olt_info', 'display_name', 'lat', 'long', 
        'postal_code', 'city_info', 'parent', 'is_tb', 'is_otb', 'device_type')


class SplitterTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitterType
        fields = "__all__"


class SplitterSerializer(serializers.ModelSerializer):
    splitter_type_info = SplitterTypeSerializer(source='splitter_type', read_only=True, required=False)
    fat_info = FATSerializerMini(source='FAT', read_only=True, required=False)
    capacity_status = serializers.SerializerMethodField('get_capacity_status')
    patch_panel_port_info = serializers.SerializerMethodField('get_pp_port_info')
    code = serializers.CharField(read_only=True)
    parent_info = serializers.SerializerMethodField()

    def get_parent_info(self, splitter):
        if (splitter.parent):
            return SplitterSerializer(splitter.parent).data

    def get_capacity_status(self, obj):
        return CheckCapacityService.get_device_available_capacity('splitter', obj.id)

    def get_pp_port_info(self, obj):
        if obj.patch_panel_port:
            cassette_port = f"{obj.patch_panel_port.cassette_number}-{obj.patch_panel_port.port_number}"
            if obj.patch_panel_port.terminal:
                patch_panel_code = obj.patch_panel_port.terminal.code
                patch_panel_id = obj.patch_panel_port.terminal.id
                return dict(id=obj.patch_panel_port.id, cassette_port=cassette_port, patch_panel_id=patch_panel_id,
                            code=patch_panel_code)
        return None


    class Meta:
        model = Splitter
        fields = "__all__"


class SplitterSerializerMini(SplitterSerializer):
    class Meta:
        model = Splitter
        fields = ('id', 'name', 'code', 'fat_info', 'patch_panel_port')


class PatchCordTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchCordType
        fields = "__all__"
        
        
class OntTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ONTType
        fields = "__all__"


class OntSerializer(serializers.ModelSerializer):
    ont_type_info = OntTypeSerializer(source='ont_type', read_only=True, required=False)
    #splitter_info = SplitterSerializerMini(source='splitter', read_only=True, required=False)

    class Meta:
        model = ONT
        fields = "__all__"


class OntSerializerMini(OntSerializer):
    class Meta:
        model = ONT
        fields = ('id', 'serial_number')


class ATBTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATBType
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    ont_info = OntSerializerMini(source='ont', read_only=True, required=False)
    cable_type_info = CableTypeSerializer(source='cable_type', read_only=True, required=False)
    ATB_info = ATBTypeSerializer(source='atb_type', read_only=True, required=False)
    patch_cord_type_info = PatchCordTypeSerializer(source='patch_cord_type', read_only=True, required=False)
    port_info = serializers.SerializerMethodField('get_port_info')
    fat_id = serializers.SerializerMethodField('get_fat_id')


    class Meta:
        model = User
        fields = ("id", "port_info", "cable_type_info", "ont_info", "ATB_info", "fat_id",
            "patch_cord_type_info", "crm_id", "cable_meterage", "lat", "long", "fiber_number_color",
            "patch_cord_length", "fqdn", "patch_cord_type", "cable_type", "atb_type")

    def get_port_info(self, obj):
        try:
            port = ReservedPorts.objects.get(ftth_user=obj)
            return ReservedPortSerializer(port).data if port else {}
        except:
            return {}

    def get_fat_id(self, obj):
        reserved_port = ReservedPorts.objects.filter(ftth_user=obj).first()
        if reserved_port:
            if reserved_port.splitter and reserved_port.splitter.FAT:
                return reserved_port.splitter.FAT.id


class HandholeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandholeType
        fields = "__all__"


class HandholeSerializer(serializers.ModelSerializer):
    type_info = HandholeTypeSerializer(source='type', read_only=True, required=False)
    display_name = serializers.CharField(source='number', read_only=True, required=False)
    city_info = CitySerializer(source="city", read_only=True, required=False)
    joint_count = serializers.SerializerMethodField('get_joint_count', read_only=True, required=False)

    def get_joint_count(self, obj):
        return obj.joint_set.count()

    class Meta:
        model = Handhole
        fields = ('id', 'type', 'number', 'is_t', 'description', 'city', 'lat', 'long', 'display_name', 'type_info',
                  'city_info', 'urban_district', 'joint_count', 'code', 'patch_panel_count')


class HandholeMapSerializer(serializers.ModelSerializer):

    class Meta:
        model = Handhole
        select_related = ('city', 'city__parent')

    def to_representation(self, instance):
        province_name, city_name, lat, long = None, None, None, None
        if instance and instance.city:
            city_name = instance.city.name
            lat = instance.city.lat
            long = instance.city.long
            province_name = instance.city.parent.name if instance.city.parent else None
        data = {
            'id': instance.id,
            'display_name': instance.number,
            'description': instance.description,
            'lat': instance.lat,
            'long': instance.long,
            'city_info': dict(id=instance.city.id, name=instance.city.name, lat=lat, long=long,
                              text=f'{province_name} / {city_name}')
        }
        return data


class JointTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = JointType
        fields = "__all__"


class JointSerializer(serializers.ModelSerializer):
    handhole_info = HandholeSerializer(source='handhole', read_only=True, required=False)
    type_info = JointTypeSerializer(source='type', read_only=True, required=False)
    patch_panel_count = serializers.SerializerMethodField('get_patch_panel_count', read_only=True, required=False)

    def get_patch_panel_count(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return Terminal.objects.filter(content_type=content_type, object_id=obj.id).count()

    class Meta:
        model = Joint
        fields = "__all__"


class HandholeRelationSerializer(serializers.ModelSerializer):
    handhole_info = HandholeSerializer(source='handhole', read_only=True, required=False)
    src_info = serializers.SerializerMethodField('get_data')

    def get_data(self, obj):
        if obj.relation_src_type.lower() == 'cabinet':
            instance = OLTCabinet.objects.get(id=obj.relation_src_id)
            object_info = OLTCabinetSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.relation_src_type.lower() in ['fat', 'ffat', 'otb', 'tb']:
            instance = FAT.objects.get(id=obj.relation_src_id)
            object_info = FATSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.relation_src_type.lower() in ['handhole', 't']:
            instance = Handhole.objects.get(id=obj.relation_src_id)
            object_info = HandholeSerializer(instance=instance, read_only=True, required=False).data
        else:
            object_info = None
        return object_info

    class Meta:
        model = HandholeRelations
        fields = "__all__"  


class MicroductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MicroductType
        fields = "__all__"


class MicroductSerializer(serializers.ModelSerializer):
    type_info = MicroductTypeSerializer(source='type', read_only=True, required=False)
    src_device_info = serializers.SerializerMethodField('get_src_data')
    dst_device_info = serializers.SerializerMethodField('get_dst_data')
    route = serializers.SerializerMethodField('fetch_route')
    city_info = CitySerializer(source="city", read_only=True, required=False)

    model_mapping = {
        'cabinet': OLTCabinet,
        'fat': FAT,
        'ffat': FAT,
        'otb': FAT,
        'tb': FAT,
        'handhole': Handhole,
        't': Handhole,
        'odc': OLTCabinet,
        'user': ReservedPorts
    }

    def get_instance(self, device_type, device_id):
        model_name = self.model_mapping.get(device_type)
        if model_name:
            return model_name.objects.get(id=device_id)
        return None

    def fetch_route(self, obj):
        items = Routes.objects.filter(device_type="microduct", device_id=obj.id).order_by("index").all()
        return RoutesSerializer(items, many=True).data

    def get_src_data(self, obj):
        instance = self.get_instance(obj.src_device_type, obj.src_device_id)
        if obj.src_device_type.lower() == 'cabinet':
            object_info = OLTCabinetSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() in ['fat', 'ffat', 'otb', 'tb']:
            object_info = FATSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() in ['handhole', 't']:
            object_info = HandholeSerializer(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() == 'odc':
            object_info = ODCSerializer(instance=instance, read_only=True, required=False).data
        elif obj.src_device_type.lower() == 'user':
            object_info = ReservedPortMiniSerializer(instance=instance, read_only=True, required=False).data
        else:
            object_info = None
        return object_info
    
    def get_dst_data(self, obj):
        instance = self.get_instance(obj.dst_device_type, obj.dst_device_id)
        if obj.dst_device_type.lower() == 'cabinet':
            object_info = OLTCabinetSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() in ['fat', 'ffat', 'otb', 'tb']:
            object_info = FATSerializerMini(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() in ['handhole', 't']:
            object_info = HandholeSerializer(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() == 'odc':
            object_info = ODCSerializer(instance=instance, read_only=True, required=False).data
        elif obj.dst_device_type.lower() == 'user':
            object_info = ReservedPortMiniSerializer(instance=instance, read_only=True, required=False).data
        else:
            object_info = None
        return object_info

    class Meta:
        model = Microduct
        fields = ('id', 'route', 'type', 'usage', 'type_info', 'channel_count', 'size', 'code', 'length', 'dst_device_type', 'dst_device_id',
                  'src_device_type', 'src_device_id', 'src_device_info', 'dst_device_info', 'city_info', 'city', 'urban_district')


class MicroductMapSerializer(MicroductSerializer):
    src_device_info = serializers.SerializerMethodField('get_src_data')
    dst_device_info = serializers.SerializerMethodField('get_dst_data')
    cables_count = serializers.SerializerMethodField('get_cables_count')

    def get_cables_count(self, obj):
        return obj.microductscables_set.filter(deleted_at__isnull=True).count()

    def get_src_data(self, obj):
        if obj.src_device_type == None:
            return None
        instance = self.get_instance(obj.src_device_type, obj.src_device_id)
        if instance:
            return dict(id=instance.id, lat=instance.lat, long=instance.long)
        else:
            return None

    def get_dst_data(self, obj):
        if obj.dst_device_type == None:
            return None
        instance = self.get_instance(obj.dst_device_type, obj.dst_device_id)
        if instance:
            return dict(id=instance.id, lat=instance.lat, long=instance.long)
        else:
            return None

    class Meta:
        model = Microduct
        fields = ('id', 'channel_count', 'size', 'code', 'cables_count', 'route', 'src_device_info', 'dst_device_info')


class MicroductMiniSerializer(serializers.ModelSerializer):
    city_info = CitySerializer(source="city", read_only=True, required=False)

    class Meta:
        model = Microduct
        fields = ('id', 'usage', 'channel_count', 'size', 'code', 'length', 'dst_device_type', 'dst_device_id',
                  'src_device_type', 'src_device_id', 'city_info', 'urban_district')


class TerminalPortMiniSerializer(serializers.ModelSerializer):
    cassette_port = serializers.SerializerMethodField('get_cassette_port')

    def get_cassette_port(self, obj):
        return f'{obj.cassette_number}-{obj.port_number}'

    class Meta:
        model = TerminalPort
        fields = ('id', 'port_number', 'cassette_number', 'cassette_port', 'cable', 'loose_color', 'core_color',
                  'out_cable', 'out_loose_color', 'out_core_color', 'is_active')


class MicroductsCablesSerializer(serializers.ModelSerializer):
    cable_info = CableSerializer(source='cable', read_only=True, required=False)
    microduct_info = MicroductMiniSerializer(source='microduct', read_only=True, required=False)

    class Meta:
        model = MicroductsCables
        fields = ('id', 'cable', 'microduct', 'loose_color', 'cable_info', 'microduct_info')


class JointsCablesSerializer(serializers.ModelSerializer):
    cable_info = CableSerializer(source='cable', read_only=True, required=False)
    joint_info = JointSerializer(source='joint', read_only=True, required=False)

    class Meta:
        model = JointsCables
        fields = ('id', 'cable', 'joint', 'loose_color', 'core_color', 'is_active', 'cable_info', 'joint_info')

class ReservedPortMiniSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField('get_display_name') 
    city_id = serializers.SerializerMethodField('get_city_id') 

    def get_display_name(self, obj):
        return obj.customer_name

    def get_city_id(self, obj):
        if obj.fat and obj.fat.city:
            return obj.fat.city.id
        return None

    class Meta:
        model = ReservedPorts
        fields = ('status_label', "display_name", "id", "status", "splitter", "leg_number", "description", "crm_username", "created_at",
                  "customer_name_en", "lat", "lng", 'patch_panel_port', "customer_name",
                  'pon_serial_number', 'postal_code', 'postal_address', 'fat', 'city_id', 'ibs_password')

class ReservedPortSerializer(ReservedPortMiniSerializer):
    patch_panel_port_info = serializers.SerializerMethodField('get_pp_port_info')
    installer_info = serializers.SerializerMethodField('get_installer_info', read_only=True, required=False)
    cabler_info = serializers.SerializerMethodField('get_cabler_info', read_only=True, required=False)
    tech_agent_info = serializers.SerializerMethodField('get_tech_agent_info', read_only=True, required=False)
    building_info = BuildingSerializer(source='building', read_only=True, required=False)

    def get_pp_port_info(self, obj):
        if obj.patch_panel_port:
            cassette_port = f"{obj.patch_panel_port.cassette_number}-{obj.patch_panel_port.port_number}"
            fat_info = None
            if obj.patch_panel_port.terminal:
                patch_panel_code = obj.patch_panel_port.terminal.code
                patch_panel_id = obj.patch_panel_port.terminal.id
                if obj.patch_panel_port.terminal.content_type.model_class() == FAT:
                    fat = FAT.objects.get(id=obj.patch_panel_port.terminal.object_id)
                    fat_info = FATSerializerMini(fat).data

                return dict(id=obj.patch_panel_port.id, cassette_port=cassette_port, patch_panel_id=patch_panel_id,
                            patch_panel_code=patch_panel_code, fat_info=fat_info)
        return None

    def get_tech_agent_info(self, obj):
        if obj.tech_agent:
            return dict(
                id=obj.tech_agent.id,
                email=obj.tech_agent.email,
                first_name=obj.tech_agent.first_name,
                last_name=obj.tech_agent.last_name,
                fa_first_name=obj.tech_agent.fa_first_name,
                fa_last_name=obj.tech_agent.fa_last_name,
                username=obj.tech_agent.username,
                tel=obj.tech_agent.tel,
                mobile_number=obj.tech_agent.mobile_number,
            )

    def get_installer_info(self, obj):
        if obj.installer:
            return dict(
                id=obj.installer.id,
                email=obj.installer.email,
                first_name=obj.installer.first_name,
                last_name=obj.installer.last_name,
                fa_first_name=obj.installer.fa_first_name,
                fa_last_name=obj.installer.fa_last_name,
                username=obj.installer.username,
                tel=obj.installer.tel,
                mobile_number=obj.installer.mobile_number,
            )

    def get_cabler_info(self, obj):
        if obj.cabler:
            return dict(
                id=obj.cabler.id,
                email=obj.cabler.email,
                first_name=obj.cabler.first_name,
                last_name=obj.cabler.last_name,
                fa_first_name=obj.cabler.fa_first_name,
                fa_last_name=obj.cabler.fa_last_name,
                username=obj.cabler.username,
                tel=obj.cabler.tel,
                mobile_number=obj.cabler.mobile_number,
            )                        
            

    class Meta:
        model = ReservedPorts
        fields = ('status_label', "display_name", "id", "status", "splitter", "leg_number", "description", "crm_username", "created_at",
                  "customer_name_en", "lat", "lng", 'patch_panel_port', 'patch_panel_port_info', "customer_name", 'ibs_password', "tech_agent_info",
                  'pon_serial_number', 'postal_code', 'postal_address', 'fat', 'installer_info', 'cabler_info', 'city_id', 'building_info',
                  'cable_type', 'cable_meterage', 'atb_type', 'patch_cord_type', 'patch_cord_length', 'fiber_number_color')


class ReservedPortFullSerializer(ReservedPortSerializer):
    splitter_info = SplitterSerializerMini(source='splitter', read_only=True, required=False)
    operator_info = UserUpdateSerializer(source='operator', read_only=True, required=False)
    olt_port_info = serializers.SerializerMethodField('get_olt_port_info')

    def get_olt_port_info(self, obj):
        patch_panel_port = obj.patch_panel_port

        if not patch_panel_port and obj.splitter:
            finalSplitter = obj.splitter
            while finalSplitter and finalSplitter.parent: # n-level parenting
                finalSplitter = finalSplitter.parent

            if finalSplitter.patch_panel_port:
                patch_panel_port = finalSplitter.patch_panel_port

        return get_olt_slot_port(patch_panel_port)

    class Meta:
        model = ReservedPorts
        fields = ('display_name', 'duration_days', 'splitter_info', 'operator_info','status_label', "id", "status", "splitter",
                  "leg_number", "description", "crm_username", "created_at", "customer_name_en", 'ibs_password', "tech_agent_info",
                  "lat", "lng", "pon_serial_number", "cancel_reason", 'olt_port_info', 'patch_panel_port', "customer_name",
                  'patch_panel_port_info', 'postal_code', 'postal_address', 'installer_info', 'cabler_info', 'city_id', 'building_info',
                  'cable_type', 'cable_meterage', 'atb_type', 'patch_cord_type', 'patch_cord_length', 'fiber_number_color')


class OntSetupSerializer(serializers.ModelSerializer):
    fat_info = FATSerializer(source='fat', read_only=True, required=False)
    confirmor_info = UserUpdateSerializer(source='confirmor', read_only=True, required=False)
    commands_list = serializers.SerializerMethodField('decode_commands')
    reserved_port_info = ReservedPortFullSerializer(source='reserved_port', read_only=True, required=False)

    def decode_commands(self, obj):
        if obj.commands:
            return json.loads(obj.commands)
        return []

    class Meta:
        model = OntSetup
        fields = "__all__"   


class OntSetupEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = OntSetup
        fields = ["installer", "ftth_ont_id", "ftth_user_id"]


class TreeOntSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='serial_number')
    _type_ = serializers.CharField(default='ont', read_only=True)

    class Meta:
        model = ONT
        fields = ['id', 'name', '_type_']


class TreeSplitterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='code')
    _type_ = serializers.CharField(default='splitter', read_only=True)
    children = TreeOntSerializer(many=True, source='ont_set')

    class Meta:
        model = Splitter
        fields = ['id', 'name', '_type_', 'children']


class TreeFatSerializer(serializers.ModelSerializer):
    children = TreeSplitterSerializer(many=True, source='splitter_set')
    _type_ = serializers.CharField(default='fat', read_only=True)

    class Meta:
        model = FAT
        fields = ['id', 'name', '_type_', 'children']


class TreeOltSerializer(serializers.ModelSerializer):
    children = TreeFatSerializer(many=True, source='fat_set')
    _type_ = serializers.CharField(default='olt', read_only=True)

    class Meta:
        model = OLT
        fields = ['id', 'name', '_type_', 'children']


class TreeCabinetSerializer(serializers.ModelSerializer):
    children = TreeOltSerializer(many=True, source='olt_set')
    _type_ = serializers.CharField(default='cabinet', read_only=True)

    class Meta:
        model = OLTCabinet
        fields = ['id', 'name', '_type_', 'children']


class OltCardSerializer(serializers.ModelSerializer):
    olt_id = serializers.PrimaryKeyRelatedField(queryset=OLT.objects.all(), source='olt')
    class Meta:
        model = OltCard
        fields = ('id', 'olt_id', 'number', 'ports_count', 'description')


class OltPortSerializer(serializers.ModelSerializer):
    card_id = serializers.PrimaryKeyRelatedField(queryset=OltCard.objects.all(), source='card')
    pp_port_id = serializers.PrimaryKeyRelatedField(queryset=TerminalPort.objects.all(), source='patch_panel_port')
    card_number = serializers.SerializerMethodField('get_card_number')
    pp_port_info = serializers.SerializerMethodField('get_pp_port_info')
    def get_card_number(self, obj):
        return obj.card.number

    def get_pp_port_info(self, obj):
        if obj.patch_panel_port:
            return dict(pp_code=obj.patch_panel_port.terminal.code,
                        cassette_port=f'{obj.patch_panel_port.cassette_number}-{obj.patch_panel_port.port_number}')
        return None
    class Meta:
        model = OltPort
        fields = ('id', 'card_id', 'card_number', 'port_number', 'pp_port_id', 'pp_port_info')


class InspectionSerializer(serializers.ModelSerializer):
    is_passed = serializers.ReadOnlyField(read_only=True)
    class Meta:
        model = Inspection
        fields = [
            'id',
            'content_type',
            'object_id',
            'point_shoot',
            'point_fusion',
            'initial_test',
            'cabinet_installation',
            'cabinet_uplink',
            'cabinet_power',
            'shoot_uplink',
            'site_code',
            'serial_number',
            'status',
            'status_label',
            'is_passed'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        content_type = instance.content_type.model
        representation['content_type'] = 'cabinet' if content_type == 'oltcabinet' else content_type
        return representation
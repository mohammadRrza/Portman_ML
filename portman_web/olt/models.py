from django.db import models
from dslam.models import City
from users.models import User as main_user
from datetime import datetime
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class Property(models.Model):

    INSPECTION_STATUS_PENDING = 1
    INSPECTION_STATUS_FAILED = 9
    INSPECTION_STATUS_SUCCESSFUL = 10

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    creator = models.ForeignKey(main_user, on_delete=models.DO_NOTHING,   related_name='creator')
    approver = models.ForeignKey(main_user, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='approver')
    is_completed = models.BooleanField(default=False, null=True, blank=True,)
    inspection_status = models.IntegerField(null=True, blank=True,)
    approved_at = models.DateTimeField(blank=True, null=True)


class AbstractProperty(models.Model):
    property = models.OneToOneField(Property, null=True, blank=True, on_delete=models.DO_NOTHING)

    class Meta:
        abstract = True


class TimeFields(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        abstract = True


class OLTType(models.Model):
    name = models.CharField(max_length=24, verbose_name='name')
    model = models.CharField(max_length=16, null=True, blank=True)
    card_count = models.IntegerField(null=True, blank=True)
    card_type = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        return self.name


class OLTCabinetType(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True)
    model = models.CharField(max_length=32, null=True, blank=True)
    core_count = models.IntegerField(null=True, blank=True)
    is_odc = models.BooleanField(null=True, blank=True, default=False)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return self.name


class OLTCabinet(AbstractProperty):
    name = models.CharField(max_length=32, null=True, blank=True)
    type = models.ForeignKey(OLTCabinetType, on_delete=models.DO_NOTHING, null=True, blank=True)
    city = models.ForeignKey(City, verbose_name='city', db_index=True,
                             on_delete=models.CASCADE, null=True)
    urban_district = models.PositiveIntegerField(null=True, blank=True)
    lat = models.CharField(max_length=32, null=True, blank=True)
    long = models.CharField(max_length=32, null=True, blank=True)
    max_capacity = models.IntegerField(null=True, blank=True, default=2)
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True)
    is_odc = models.BooleanField(default=False,  null=True, blank=True)
    property_number = models.CharField(max_length=16, null=True, blank=True)
    cooling_type = models.CharField(max_length=16, null=True, blank=True)
    battery_type = models.CharField(max_length=16, null=True, blank=True)
    battery_count = models.IntegerField(null=True, blank=True, default=1)
    rectifier_type = models.CharField(max_length=16, null=True, blank=True)
    rectifier_property_number = models.CharField(max_length=16, null=True, blank=True)
    power_meter_type = models.CharField(max_length=16, null=True, blank=True)
    power_payment_id = models.CharField(max_length=16, null=True, blank=True)
    key_holder = models.CharField(max_length=24, null=True, blank=True)
    cabinet_password = models.CharField(max_length=24, null=True, blank=True)
    crm_id = models.IntegerField(null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    install_manager = models.ForeignKey(main_user, on_delete=models.DO_NOTHING, related_name='install_manager', null=True, blank=True)


    def __str__(self):
        return self.name

    @staticmethod
    def soft_delete(instance):
        olts = instance.olt_set.all().exclude(deleted_at__isnull=False)
        for olt in olts:
            OLT.soft_delete(olt)
        instance.deleted_at = datetime.now()
        instance.save()

    @property
    def code(self):
        try:
            province_abbr = self.city.parent.abbr if self.city and self.city.parent else ''
            city_abbr = self.city.abbr if self.city else ''
            urban_district = self.urban_district if self.urban_district else ''
            obj_type = 'ODC' if self.is_odc else 'C'
            return f'{province_abbr}.{city_abbr}.Z{urban_district}.{obj_type}{self.name}'
        except:
            return '--unable-to-generate-code--'


class OLT(AbstractProperty):
    cabinet = models.ForeignKey(OLTCabinet, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    olt_number = models.IntegerField(null=True, blank=True, default=0)
    olt_type = models.ForeignKey(OLTType, on_delete=models.CASCADE, null=True, blank=True)
    ip = models.CharField(max_length=15, unique=True, null=True, blank=True)
    max_capacity = models.IntegerField(null=True, blank=True, default=32)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    profile_id = models.IntegerField(null=True, blank=True, default=0)
    ont_port_id = models.IntegerField(null=True, blank=True, default=0)
    mg_id = models.IntegerField(null=True, blank=True, default=0)
    priority = models.IntegerField(null=True, blank=True, default=0)
    version = models.CharField(max_length=32, null=True, blank=True, )
    active = models.BooleanField(default=True, null=True, blank=True)
    status = models.CharField(max_length=10, null=True, blank=True, default='new')
    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_duration = models.IntegerField(null=True, blank=True)
    uptime = models.CharField(max_length=32, blank=True, null=True)
    hostname = models.CharField(max_length=32, blank=True, null=True)
    conn_type = models.CharField(max_length=20, null=True, blank=True)
    get_snmp_community = models.CharField(max_length=24, null=True, blank=True)
    set_snmp_community = models.CharField(max_length=24, null=True, blank=True)
    snmp_port = models.IntegerField(null=True, blank=True)
    snmp_timeout = models.IntegerField(null=True, blank=True, default=3)
    telnet_username = models.CharField(max_length=24, null=True, blank=True)
    telnet_password = models.CharField(max_length=24, null=True, blank=True)
    slot_count = models.IntegerField(null=True, blank=True, default=17)
    port_count = models.IntegerField(null=True, blank=True, default=72)
    availability_start_time = models.DateTimeField(auto_now_add=True)
    down_seconds = models.BigIntegerField(default=0, null=True, blank=True)
    fqdn = models.CharField(max_length=128, null=True, blank=True)
    vlan_number = models.IntegerField(null=True, blank=True, default=0)
    gemport = models.IntegerField(null=True, blank=True, default=10)
    inbound_index = models.IntegerField(null=True, blank=True, default=500)
    outbound_index = models.IntegerField(null=True, blank=True, default=500)
    last_backup_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    @property
    def code(self):
        try:
            return f'{self.cabinet.code}.OLT{self.name}'
        except:
            return '--unable-to-generate-code--'

    @staticmethod
    def soft_delete(instance):
        fats = instance.fat_set.all().exclude(deleted_at__isnull=False)
        for fat in fats:
            FAT.soft_delete(fat)
        instance.deleted_at = datetime.now()
        instance.save()

    @property
    def get_olt_availability(self):
        now = datetime.now()
        total = (now - self.availability_start_time).total_seconds() / 1200
        return 100 - (((self.down_seconds / 1200) / total) * 100)

    def get_info(self):
        return dict(
            id=self.id,
            name=self.name,
            ip=self.ip,
            active=self.active,
            status=self.status,
            last_sync=self.last_sync,
            conn_type=self.conn_type,
            get_snmp_community=self.get_snmp_community,
            set_snmp_community=self.set_snmp_community,
            snmp_port=self.snmp_port,
            telnet_username=str(self.telnet_username),
            telnet_password=str(self.telnet_password),
            slot_count=self.slot_count,
            port_count=self.port_count,
            snmp_timeout=self.snmp_timeout,
            olt_type=self.olt_type.model,
            olt_type_name=self.olt_type.name,
            last_sync_duration=self.last_sync_duration,
            created_at=self.created_at,
            updated_at=self.updated_at,
            olt_availability=self.get_olt_availability,
            hostname=self.hostname,
            fqdn=self.fqdn,
            uptime=self.uptime,
            vlan_number=self.vlan_number,
            outbound_index=self.outbound_index,
            inbound_index=self.inbound_index,
            gemport=self.gemport,
            profile_id=self.profile_id,
            ont_port_id=self.ont_port_id,
            mg_id=self.mg_id,
            priority=self.priority,
            max_capacity=self.max_capacity
        )


class OLTCommand(models.Model):
    text = models.CharField(max_length=128, verbose_name='name', unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.text


class OLTTypeCommand(models.Model):
    command = models.ForeignKey(OLTCommand, on_delete=models.CASCADE)
    olt_type = models.ForeignKey(OLTType, on_delete=models.CASCADE)

    # def __str__(self):
    #     return self.command


class Terminal(AbstractProperty):
    port_count = models.IntegerField(blank=True, null=True)
    cassette_count = models.IntegerField(blank=True, null=True)
    code = models.CharField(max_length=32, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, blank=True, null=True,)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CableType(models.Model):
    color = models.CharField(max_length=16, null=True, blank=True)
    label = models.CharField(max_length=16, null=True, blank=True)
    type = models.CharField(max_length=16, null=True, blank=True)
    serial = models.CharField(max_length=24, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    core_count = models.IntegerField(null=True, blank=True)
    manufacturer = models.CharField(max_length=24, null=True, blank=True)


class Cable(AbstractProperty):
    meterage = models.FloatField(null=True, blank=True)
    type = models.ForeignKey(CableType, on_delete=models.DO_NOTHING)
    code = models.CharField(max_length=128, null=True, blank=True)
    plan_code = models.CharField(max_length=32, null=True, blank=True)
    uplink = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True)
    usage = models.CharField(max_length=32, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True, blank=True)
    length = models.FloatField(null=True, blank=True)
    dst_device_type = models.CharField(max_length=32, null=True, blank=True)
    dst_device_id = models.IntegerField(blank=True, null=True)
    src_device_type = models.CharField(max_length=32, null=True, blank=True)
    src_device_id = models.IntegerField(blank=True, null=True)
    dst_extra_cable = models.FloatField(null=True, blank=True)
    src_extra_cable = models.FloatField(null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def soft_delete(self, *args, **kwargs):
        self.microductscables_set.all().update(deleted_at=datetime.now())
        self.jointscables_set.all().update(deleted_at=datetime.now())
        TerminalPort.objects.filter(cable=self).update(cable=None, core_color=None, loose_color=None)
        TerminalPort.objects.filter(out_cable=self).update(out_cable=None, out_core_color=None, out_loose_color=None)
        self.deleted_at = datetime.now()
        self.save()

    def generate_code(self):
        try:
            model_mapping = {
                'cabinet': OLTCabinet,
                'fat': FAT,
                'handhole': Handhole,
                't': Handhole,
                'odc': OLTCabinet,
                'ffat': FAT,
                'otb': FAT,
                'tb': FAT,
                'user': ReservedPorts
            }
            src_type = self.src_device_type
            src_model = model_mapping.get(src_type)
            src_obj = src_model.objects.get(pk=self.src_device_id)

            dst_type = self.dst_device_type
            dst_model = model_mapping.get(dst_type)
            dst_obj = dst_model.objects.get(pk=self.dst_device_id)

            src_name = src_obj.number if src_type in ['handhole', 't'] else src_obj.name
            dst_name = dst_obj.number if dst_type in ['handhole', 't'] else dst_obj.name

            microduct_cable = self.microductscables_set.filter(deleted_at__isnull=True).first()
            if microduct_cable:
                code = (f"{src_type}{src_name}.{dst_type}{dst_name}.{self.usage}"
                        f".{microduct_cable.microduct.channel_count}.{microduct_cable.loose_color}"
                        f".{self.type.core_count}core.{self.type.type}")
            else:
                code = (f"{src_type}{src_name}.{dst_type}{dst_name}.{self.usage}"
                        f".{self.type.core_count}core.{self.type.type}")
            return code

        except:
            return '--unable-to-generate-code--'

    def save(self, *args, **kwargs):
        self.code = self.generate_code()
        super().save(*args, **kwargs)


class TerminalPort(models.Model):
    port_number = models.IntegerField(blank=True, null=True)
    cassette_number = models.IntegerField(blank=True, null=True)
    terminal = models.ForeignKey(Terminal, on_delete=models.DO_NOTHING)
    cable = models.ForeignKey(Cable, on_delete=models.DO_NOTHING, null=True, blank=True,  related_name='input_cable')
    loose_color = models.CharField(max_length=32, null=True, blank=True)
    core_color = models.CharField(max_length=32, null=True, blank=True)
    out_cable = models.ForeignKey(Cable, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='output_cable')
    out_loose_color = models.CharField(max_length=32, null=True, blank=True)
    out_core_color = models.CharField(max_length=32, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    in_splitter = models.ForeignKey('Splitter',  null=True, blank=True, on_delete=models.DO_NOTHING)
    splitter_leg_number = models.IntegerField(null=True, blank=True,)
    olt_port = models.ForeignKey('OltPort', null=True, blank=True, on_delete=models.DO_NOTHING)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Building(TimeFields, AbstractProperty):
    name = models.CharField(max_length=64, null=True, blank=True)
    phone = models.CharField(max_length=24, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True, blank=True)
    urban_district = models.PositiveIntegerField(null=True, blank=True)
    unit_count = models.IntegerField(blank=True, null=True, default=1)
    postal_code = models.CharField(max_length=24, null=True, blank=True)
    postal_address = models.CharField(max_length=256, null=True, blank=True)

    def soft_delete(self, *args, **kwargs):
        self.deleted_at = datetime.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()

    @property
    def code(self):
        try:
            province_abbr = self.city.parent.abbr if self.city and self.city.parent else ''
            city_abbr = self.city.abbr if self.city else ''
            urban_district = self.urban_district if self.urban_district else ''
            return f'{province_abbr}.{city_abbr}.Z{urban_district}.B{self.id + 99}'
        except:
            return '--unable-to-generate-code--'

class FATType(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True)
    model = models.CharField(max_length=32, null=True, blank=True)
    port_count = models.IntegerField(null=True, blank=True, default=8)

    def __str__(self):
        return self.name


class FAT(AbstractProperty):
    name = models.CharField(max_length=32, null=True, blank=True, default='')
    address = models.TextField(null=True, blank=True)
    urban_district = models.PositiveIntegerField(null=True, blank=True)
    fat_type = models.ForeignKey(FATType, on_delete=models.DO_NOTHING, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, blank=True, null=True)
    is_otb = models.BooleanField(default=False, null=True, blank=True)
    is_tb = models.BooleanField(default=False, null=True, blank=True)
    fat_splitter = models.ForeignKey('Splitter', on_delete=models.DO_NOTHING, blank=True, null=True)
    leg_number = models.IntegerField(null=True, blank=True)
    max_capacity = models.IntegerField(null=True, blank=True, default=4)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    olt = models.ForeignKey(OLT, on_delete=models.DO_NOTHING, blank=True, null=True)
    patch_panel_port = models.ForeignKey(TerminalPort, on_delete=models.DO_NOTHING, blank=True, null=True)
    lat = models.CharField(max_length=32, null=True, blank=True)
    long = models.CharField(max_length=32, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    postal_code = models.CharField(max_length=16, null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.DO_NOTHING, null=True, blank=True)
    install_manager = models.ForeignKey(main_user, on_delete=models.DO_NOTHING, related_name='fat_install_manager', null=True, blank=True)



    def __str__(self):
        return self.code

    @staticmethod
    def soft_delete(instance):
        splitters = instance.splitter_set.all().exclude(deleted_at__isnull=False)
        f_fats = instance.fat_set.all().exclude(deleted_at__isnull=False)
        for splitter in splitters:
            Splitter.soft_delete(splitter)
        for f_fat in f_fats:
            FAT.soft_delete(f_fat)
        instance.deleted_at = datetime.now()
        instance.save()

    @property
    def code(self):
        try:
            if self.parent is None:
                prefix_code = self.olt.code if self.olt else ''
                obj_type = 'F'
            else:
                prefix_code = self.fat_splitter.code if self.fat_splitter else self.parent.code
                obj_type = 'OTB' if self.is_otb else 'FF'
                obj_type = 'TB' if self.is_tb else obj_type
            return f'{prefix_code}.{obj_type}{self.name}'
        except:
            return '--unable-to-generate-code--'

    @property
    def city(self):
        if self.olt and self.olt.cabinet and self.olt.cabinet.city:
            return self.olt.cabinet.city
        return None


class SplitterType(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True)
    model = models.CharField(max_length=32, null=True, blank=True)
    legs_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Splitter(AbstractProperty):
    name = models.CharField(max_length=32, null=True, blank=True)
    splitter_type = models.ForeignKey(SplitterType, on_delete=models.CASCADE, blank=True, null=True)
    max_capacity = models.IntegerField(null=True, blank=True, default=32)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    FAT = models.ForeignKey(FAT, on_delete=models.CASCADE, blank=True, null=True)
    patch_panel_port = models.ForeignKey(TerminalPort, null=True, blank=True, on_delete=models.DO_NOTHING)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    parent_leg_number = models.IntegerField(null=True, blank=True)
    #space = models.CharField(max_length=16, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.code

    @staticmethod
    def soft_delete(instance):
        child_splitters = instance.splitter_set.all().exclude(deleted_at__isnull=False)
        f_fats = instance.fat_set.all().exclude(deleted_at__isnull=False)
        for f_fat in f_fats:
            FAT.soft_delete(f_fat)
        instance.deleted_at = datetime.now()
        instance.patch_panel_port = None
        TerminalPort.objects.filter(in_splitter=instance).update(in_splitter=None, splitter_leg_number=None)
        instance.save()
        for child in child_splitters:
            Splitter.soft_delete(child)
    @property
    def code(self):
        try:
            prefix_code = self.FAT.code if self.FAT else ''
            return f'{prefix_code}.S{self.name}'
        except:
            return '--unable-to-generate-code--'


    def get_reserved_port_error(self, reserved_ports):
        error_data = {
            "message": "One or more reserved ports are in use and the splitter can't be deleted.",
            "type": "reserved_port",
            "objects": [
                {
                    "id": port.id,
                    "crm_username": port.crm_username,
                    "leg_number": port.leg_number
                }
                for port in reserved_ports
            ]
        }
        return error_data

    def get_fat_error(self, fats):
        error_data = {
            "message": "One or more fat are in use and the splitter can't be deleted.",
            "type": "fat",
            "objects": [
                {
                    "id": fat.id,
                    "name": fat.name,
                    "code": fat.code,
                    "leg_number": fat.leg_number
                }
                for fat in fats
            ]
        }
        return error_data

    def can_delete(self):
        errors = []
        in_use_reserved_ports = self.reservedports_set.all()
        if in_use_reserved_ports:
            errors.append(self.get_reserved_port_error(in_use_reserved_ports))

        in_use_fats = self.fat_set.filter(deleted_at__isnull=True)
        if in_use_fats:
            errors.append(self.get_fat_error(in_use_fats))
        return errors


class PatchCordType(models.Model):
    mode = models.CharField(max_length=16, null=True, blank=True)


class ONTType(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True)
    model = models.CharField(max_length=32, null=True, blank=True)
    fast_port_count = models.IntegerField(null=True, blank=True)
    gig_port_count = models.IntegerField(null=True, blank=True)
    band_count = models.IntegerField(null=True, blank=True)
    antenna_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class ONT(AbstractProperty):
    serial_number = models.CharField(max_length=24, null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    mac_address = models.CharField(max_length=24, null=True, blank=True)
    profile = models.CharField(max_length=24, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    olt_slot_number = models.IntegerField(null=True, blank=True)
    olt_port_number = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    ont_type = models.ForeignKey(ONTType, on_delete=models.CASCADE, null=True, blank=True)

    @staticmethod
    def soft_delete(instance):
        users = instance.user_set.all().exclude(deleted_at__isnull=False)
        for user in users:
            User.soft_delete(user)
        instance.deleted_at = datetime.now()
        instance.save()


class ATBType(models.Model):
    name = models.CharField(max_length=32, null=True, blank=True)
    model = models.CharField(max_length=32, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class User(AbstractProperty):
    ont = models.ForeignKey(ONT, on_delete=models.CASCADE, null=True, blank=True)
    cable_type = models.ForeignKey(CableType, on_delete=models.CASCADE, null=True, blank=True)
    crm_id = models.IntegerField(null=True, blank=True)
    cable_meterage = models.FloatField(null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    lat = models.CharField(max_length=32, null=True, blank=True)
    long = models.CharField(max_length=32, null=True, blank=True)
    fqdn = models.CharField(max_length=32, null=True, blank=True)
    atb_type = models.ForeignKey(ATBType, on_delete=models.CASCADE, null=True, blank=True)
    fiber_number_color = models.CharField(max_length=24, null=True, blank=True)
    patch_cord_length = models.PositiveIntegerField(null=True, blank=True)
    patch_cord_type = models.ForeignKey(PatchCordType, on_delete=models.DO_NOTHING, null=True, blank=True)

    @staticmethod
    def soft_delete(instance):
        instance.deleted_at = datetime.now()
        instance.save()


class HandholeType(AbstractProperty):
    model = models.CharField(max_length=16, null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    dem_width = models.FloatField(null=True, blank=True)
    dem_height = models.FloatField(null=True, blank=True)
    dem_depth = models.FloatField(null=True, blank=True)
    type = models.CharField(max_length=16, null=True, blank=True)
    material = models.CharField(max_length=16, null=True, blank=True)
    duct_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.model


class Handhole(AbstractProperty):
    type = models.ForeignKey(HandholeType, on_delete=models.DO_NOTHING, blank=True, null=True)
    number = models.CharField(max_length=24, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True, blank=True)
    urban_district = models.PositiveIntegerField(null=True, blank=True)
    lat = models.CharField(max_length=32, null=True, blank=True)
    long = models.CharField(max_length=32, null=True, blank=True)
    is_t = models.BooleanField(null=True, blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['number', 'city'], name='number_city_idx'),
            models.Index(fields=['city'], name='city_idx'),
        ]

    @staticmethod
    def soft_delete(instance):
        joints = instance.joint_set.all()
        for joint in joints:
            Joint.soft_delete(joint)
        instance.deleted_at = datetime.now()
        instance.save()

    @property
    def code(self):
        try:
            province_abbr = self.city.parent.abbr if self.city and self.city.parent else ''
            city_abbr = self.city.abbr if self.city else ''
            urban_district = self.urban_district if self.urban_district else ''
            object_type = 'T' if self.is_t else 'H'
            return f'{province_abbr}.{city_abbr}.Z{urban_district}.{object_type}{self.number}'
        except:
            return '--unable-to-generate-code--'

    @property
    def patch_panel_count(self):
        joint_ids = self.joint_set.values_list('id', flat=True)
        patch_panel_count = Terminal.objects.filter(
            content_type=ContentType.objects.get_for_model(Joint),
            object_id__in=joint_ids
        ).count()
        return patch_panel_count

    @property
    def name(self):
        return self.number


class JointType(models.Model):
    name = models.CharField(max_length=24, null=True, blank=True)
    model = models.CharField(max_length=24, null=True, blank=True)

    def __str__(self):
        return self.model


class Joint(AbstractProperty):
    code = models.CharField(max_length=24, null=True, blank=True)
    handhole = models.ForeignKey(Handhole, on_delete=models.DO_NOTHING)
    type = models.ForeignKey(JointType, on_delete=models.DO_NOTHING)

    @staticmethod
    def soft_delete(instance):
        joints_cables = instance.jointscables_set.all().exclude(deleted_at__isnull=False)
        for joints_cable in joints_cables:
            JointsCables.soft_delete(joints_cable)
        instance.delete()


class HandholeRelations(models.Model):
    handhole = models.ForeignKey(Handhole, on_delete=models.DO_NOTHING)
    relation_src_type = models.CharField(max_length=16, null=True, blank=True)
    relation_src_id = models.IntegerField(null=True, blank=True)
    extra_cable = models.FloatField(null=True, blank=True)


class UsersAuditLog(models.Model):
    user = models.ForeignKey(main_user, on_delete=models.DO_NOTHING, null=True, blank=True)
    model_name = models.CharField(max_length=16)
    instance_id = models.IntegerField(blank=True, null=True)
    action = models.CharField(max_length=24)
    description = models.TextField(blank=True, null=True)
    log_date = models.DateTimeField(auto_now_add=True)


class MicroductType(models.Model):
    title = models.CharField(max_length=32, null=True, blank=True)


class Microduct(AbstractProperty):
    type = models.ForeignKey(MicroductType, on_delete=models.DO_NOTHING, null=True, blank=True)
    usage = models.CharField(max_length=32, null=True, blank=True)
    channel_count = models.IntegerField(blank=True, null=True)
    size = models.CharField(max_length=16, null=True, blank=True)
    code = models.CharField(max_length=128, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING, null=True, blank=True)
    urban_district = models.PositiveIntegerField(null=True, blank=True)
    length = models.FloatField(null=True, blank=True)
    dst_device_type = models.CharField(max_length=32, null=True, blank=True)
    dst_device_id = models.IntegerField(blank=True, null=True)
    src_device_type = models.CharField(max_length=32, null=True, blank=True)
    src_device_id = models.IntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        microuct_cables = self.microductscables_set.filter(deleted_at__isnull=True)
        for microuct_cable in microuct_cables:
            microuct_cable.cable.save()


class Routes(models.Model):
    device_type = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    device_id = models.IntegerField(blank=True, null=True, db_index=True)
    index = models.IntegerField(blank=True, null=True)
    lat = models.CharField(max_length=24)
    lng = models.CharField(max_length=24)


class MicroductsCables(models.Model):
    cable = models.ForeignKey(Cable, on_delete=models.DO_NOTHING)
    microduct = models.ForeignKey(Microduct, on_delete=models.DO_NOTHING)
    loose_color = models.CharField(max_length=32, null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.cable.save()


class JointsCables(models.Model):
    cable = models.ForeignKey(Cable, on_delete=models.DO_NOTHING)
    joint = models.ForeignKey(Joint, on_delete=models.DO_NOTHING)
    loose_color = models.CharField(max_length=32, null=True, blank=True)
    core_color = models.CharField(max_length=32, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def soft_delete(instance):
        instance.deleted_at = datetime.now()
        instance.save()

class ReservedPorts(models.Model):
    STATUS_CORRUPTED = -2
    STATUS_CANCELED  = -1
    STATUS_RESERVED  = 0
    STATUS_READY_TO_CONFIG = 1
    STATUS_READY_TO_INSTALL = 2
    STATUS_ALLOCATED = 10
    STATUS_RELEASED  = 20

    NOT_FREE_STATUZ = [STATUS_CORRUPTED, STATUS_RESERVED, STATUS_ALLOCATED, STATUS_READY_TO_CONFIG, STATUS_READY_TO_INSTALL]

    splitter = models.ForeignKey(Splitter,  null=True, blank=True, on_delete=models.DO_NOTHING)
    leg_number = models.IntegerField(db_index=True,  null=True, blank=True,)
    duration_days = models.IntegerField(db_index=True, default=7)
    created_at = models.DateTimeField(auto_now_add=True)
    crm_id = models.CharField(max_length=16, null=True, blank=True)
    crm_username = models.CharField(max_length=24, null=True, blank=True)
    ibs_password = models.CharField(max_length=32, null=True, blank=True)
    status = models.IntegerField(db_index=True, default=0, blank=True)
    operator = models.ForeignKey(main_user, on_delete=models.DO_NOTHING,null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    customer_name = models.CharField(null=True, blank=True, max_length=128)
    customer_name_en = models.CharField(null=True, blank=True, max_length=64)
    lat = models.CharField(max_length=24)
    lng = models.CharField(max_length=24)
    #ftth_user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    cancel_reason = models.TextField(null=True, blank=True)
    pon_serial_number = models.CharField(max_length=64, null=True, blank=True)
    patch_panel_port = models.ForeignKey(TerminalPort, null=True, blank=True, on_delete=models.DO_NOTHING)
    postal_code = models.CharField(max_length=24, null=True, blank=True)
    postal_address = models.CharField(max_length=256, null=True, blank=True)
    fat = models.ForeignKey(FAT, null=True, blank=True, on_delete=models.DO_NOTHING)
    installer = models.ForeignKey(main_user, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='installer')
    cabler = models.ForeignKey(main_user, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='cabler')
    tech_agent = models.ForeignKey(main_user, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='tech_agent')
    building = models.ForeignKey(Building, on_delete=models.DO_NOTHING, null=True, blank=True)
    cable_type = models.ForeignKey(CableType, on_delete=models.CASCADE, null=True, blank=True)
    cable_meterage = models.FloatField(null=True, blank=True)
    atb_type = models.ForeignKey(ATBType, on_delete=models.CASCADE, null=True, blank=True)
    fiber_number_color = models.CharField(max_length=24, null=True, blank=True)
    patch_cord_length = models.PositiveIntegerField(null=True, blank=True)
    patch_cord_type = models.ForeignKey(PatchCordType, on_delete=models.DO_NOTHING, null=True, blank=True)

    @property
    def name(self):
        return self.crm_username

    @property
    def long(self):
        return self.lng
    
    @property
    def status_label(self):
        if self.status == self.STATUS_CANCELED:
            return _("Cenceled")
        elif self.status == self.STATUS_ALLOCATED:
            return _("Allocated")
        elif self.status == self.STATUS_CORRUPTED:
            return _("Corrupted")
        elif self.status == self.STATUS_RELEASED:
            return _("Released")
        elif self.status == self.STATUS_READY_TO_CONFIG:
            return _("Ready To Config")
        elif self.status == self.STATUS_READY_TO_INSTALL:
            return _("Ready To Install")
        return _("Reserved")


    @staticmethod
    def setAllocated(id):
        row = ReservedPorts.objects.get(pk=id)
        if (row == None):
            return False
        row.status = ReservedPorts.STATUS_ALLOCATED
        return row.save()


class OntSetup(models.Model):
    fat = models.ForeignKey(FAT, on_delete=models.DO_NOTHING)
    pon_serial_number = models.CharField(max_length=64)
    equipment_id = models.CharField(max_length=32, blank=True, null=True)
    confirmor = models.ForeignKey(main_user, on_delete=models.DO_NOTHING)
    installer = models.CharField(max_length=64, blank=True, null=True)
    customer_name = models.CharField(max_length=64)
    customer_username = models.CharField(max_length=32)
    lat = models.CharField(max_length=24)
    lng = models.CharField(max_length=24)
    slot = models.IntegerField(blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    confirm_ont_id = models.IntegerField(blank=True, null=True)
    ftth_ont_id = models.IntegerField(blank=True, null=True)
    ftth_user_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    commands = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    reserved_port = models.ForeignKey(ReservedPorts, on_delete=models.DO_NOTHING, blank=True, null=True)


class OltCard(AbstractProperty):
    olt = models.ForeignKey(OLT, on_delete=models.DO_NOTHING)
    number = models.IntegerField(default=1)
    ports_count = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)


class OltPort(AbstractProperty):
    card = models.ForeignKey(OltCard, on_delete=models.DO_NOTHING)
    port_number = models.IntegerField(default=1)
    patch_panel_port = models.ForeignKey(TerminalPort, null=True, blank=True, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)


class Inspection(TimeFields):

    STATUS_CHECKING_START_POINT_BY_ZONE_HEAD = 1
    STATUS_CHECKING_START_POINT_RESULT_BY_ZONE_EXPERT = 2
    STATUS_CHECKING_DATA_RESULT_BY_ZONE_EXPERT = 3
    STATUS_CHECKING_REQUEST_BY_HDQRTR_CONFIRMOR = 4
    STATUS_CONVERTERY_ITEMS = 5
    STATUS_EDIT_DATA = 6
    STATUS_COMPLETED = 10

    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    point_shoot = models.BooleanField(default=False, null=True, blank=True)
    point_fusion = models.BooleanField(default=False, null=True, blank=True)
    initial_test = models.BooleanField(default=False, null=True, blank=True)
    cabinet_installation = models.BooleanField(default=False, null=True, blank=True)
    cabinet_uplink = models.BooleanField(default=False, null=True, blank=True)
    cabinet_power = models.BooleanField(default=False, null=True, blank=True)
    shoot_uplink = models.BooleanField(default=False, null=True, blank=True)
    status = models.IntegerField(blank=True, null=True)
    site_code = models.CharField(max_length=64, blank=True, null=True)
    serial_number = models.CharField(max_length=64, blank=True, null=True)

    @property
    def is_passed(self):
        if (self.status == self.STATUS_COMPLETED):
            return True
        else:
            return False

    @property
    def status_label(self):
        if self.status == self.STATUS_COMPLETED:
            return "Completed"
        else:
            return "None Defined"

    def change_passing_status(self):
        new_status = Property.INSPECTION_STATUS_SUCCESSFUL if self.is_passed else Property.INSPECTION_STATUS_FAILED
        Property.objects.filter(content_type=self.content_type,
                                object_id=self.object_id).update(inspection_status=new_status)

    def save(self, *args, **kwargs):
        self.change_passing_status()
        super().save(*args, **kwargs)

    def soft_delete(self, *args, **kwargs):
        self.deleted_at = datetime.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()


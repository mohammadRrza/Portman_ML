from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import architect
from datetime import datetime
from dslam.models import DSLAM
from dslam.models import City as ProvinceCity

from users.models import User


class ContactType(models.Model):
    title = models.CharField(max_length=256)

    def __str__(self):
        return self.title


class Contact(models.Model):
    # contact_dslam = models.ForeignKey(DSLAM,db_index=True, on_delete=models.CASCADE)
    contact_type = models.ForeignKey(ContactType, db_index=True, on_delete=models.CASCADE)
    contact_name = models.CharField(max_length=256)
    phone = models.CharField(max_length=256)
    mobile_phone = models.CharField(max_length=256)
    contact_email = models.CharField(max_length=256)
    rastin_contact_id = models.CharField(max_length=256)

    def __str__(self):
        return self.contact_name


class PortmapState(models.Model):
    description = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.description


class Province(models.Model):
    provinceId = models.IntegerField(db_index=True, blank=True, null=True)
    provinceName = models.CharField(max_length=256, blank=True, null=True)
    externalId = models.IntegerField(db_index=True, blank=True, null=True)
    shaskam_Url = models.CharField(max_length=256, blank=True, null=True)
    shaskam_Username = models.CharField(max_length=256, blank=True, null=True)
    Shaskam_Password = models.CharField(max_length=256, blank=True, null=True)
    Shaskam_CompanyId = models.IntegerField(db_index=True, blank=True, null=True)
    TCIId = models.IntegerField(db_index=True, blank=True, null=True)

    def __str__(self):
        return self.provinceName


class City(models.Model):
    cityId = models.IntegerField(db_index=True, blank=True, null=True)
    cityName = models.CharField(max_length=256, blank=True, null=True)
    provinceId = models.IntegerField(db_index=True, blank=True, null=True)
    externalId = models.CharField(max_length=256, blank=True, null=True)
    areaCode = models.CharField(max_length=256, blank=True, null=True)
    shaskam_CityId = models.CharField(max_length=256, blank=True, null=True)
    TCIId = models.IntegerField(db_index=True, blank=True, null=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)

    def __str__(self):
        return self.cityName


class CenterType(models.Model):
    description = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.description


class PortType(models.Model):
    description = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.description


class TelecommunicationCenters(models.Model):
    telecomCenterId = models.IntegerField(max_length=1, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    active = models.IntegerField(db_index=True, blank=True, null=True)
    areaId = models.IntegerField(db_index=True, blank=True, null=True)
    externalId = models.IntegerField(db_index=True, blank=True, null=True)
    externalTelcoName = models.CharField(max_length=256, blank=True, null=True)
    activeInBitStream = models.BooleanField()
    CRAId = models.IntegerField(max_length=1, blank=True, null=True)
    TCIId = models.IntegerField(db_index=True, blank=True, null=True)
    centerTypeId = models.ForeignKey(CenterType, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Order(models.Model):
    rastin_order_id = models.IntegerField(db_index=True, blank=True, null=True)
    order_contact_id = models.IntegerField(db_index=True, blank=True, null=True)
    ranjePhoneNumber = models.CharField(max_length=256, blank=True, null=True)
    username = models.CharField(max_length=256, blank=True, null=True)
    user_id = models.IntegerField(db_index=True, blank=True, null=True)
    slot_number = models.IntegerField(db_index=True, blank=True, null=True)
    port_number = models.IntegerField(db_index=True, blank=True, null=True)
    telco_row = models.IntegerField(db_index=True, blank=True, null=True)
    telco_column = models.IntegerField(db_index=True, blank=True, null=True)
    telco_connection = models.IntegerField(db_index=True, blank=True, null=True)
    fqdn = models.CharField(max_length=256, blank=True, null=True)
    status = models.ForeignKey(PortmapState, on_delete=models.CASCADE)
    dslam = models.ForeignKey(DSLAM, on_delete=models.CASCADE, null=True, blank=True)
    port_type = models.ForeignKey(PortType, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.rastin_order_id


class FarzaneganProvider(models.Model):
    provider_name = models.CharField(max_length=250)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

    def __str__(self):
        return self.provider_name


class FarzaneganProviderData(models.Model):
    provider = models.ForeignKey(FarzaneganProvider, on_delete=models.CASCADE, related_name='provider_total_data')
    created = models.DateTimeField(auto_now_add=True)
    total_traffic = models.IntegerField()
    used_traffic = models.IntegerField()
    remain_traffic = models.IntegerField()
    total_numbers = models.IntegerField()
    used_numbers = models.IntegerField()
    remain_numbers = models.IntegerField()
    total_data_volume = models.FloatField()


class FarzaneganTDLTE(models.Model):
    provider = models.ForeignKey(FarzaneganProvider, on_delete=models.CASCADE, related_name='provider_data')
    date_key = models.DateField()
    provider_number = models.CharField(max_length=32)
    customer_msisdn = models.CharField(max_length=32)
    total_data_volume_income = models.CharField(max_length=32)
    owner_username = models.CharField(max_length=64)


class PishgamanNote(models.Model):
    province = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    telecom_center = models.CharField(max_length=250, blank=True, null=True)
    problem_desc = models.TextField(blank=True, null=True)
    register_time = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=120)
    status = models.IntegerField(blank=True, null=True)
    done_time = models.DateTimeField(blank=True, null=True)


class PishgamanNoteLog(models.Model):
    operator = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    note_id = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=12, null=True, blank=True)
    action_time = models.DateTimeField(auto_now=True)


class DataLocationsLog(models.Model):
    username = models.CharField(max_length=32, null=True, blank=True)
    new_ip = models.CharField(max_length=32, null=True, blank=True)
    action = models.CharField(max_length=15, null=True, blank=True)
    old_ip = models.CharField(max_length=32, null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    log_date = models.DateTimeField(null=True, blank=True, auto_now=True)
    status = models.CharField(max_length=32, null=True, blank=True)

    def __str__(self):
        return self.username


class TechnicalUser(models.Model):
    username = models.CharField(max_length=64)
    title = models.CharField(max_length=254, null=True, blank=True)
    type = models.CharField(max_length=32)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)


class TechnicalProfile(models.Model):
    host = models.CharField(max_length=254)
    host_id = models.CharField(max_length=12)
    item = models.CharField(max_length=254)
    item_id = models.CharField(max_length=12)
    province = models.ForeignKey(ProvinceCity, on_delete=models.DO_NOTHING,  related_name='province_id', default=1)
    city = models.ForeignKey(ProvinceCity, on_delete=models.DO_NOTHING,  related_name='city_id', default=1627)
    service = models.CharField(max_length=32)
    category = models.CharField(max_length=32)
    technical_user = models.ForeignKey(TechnicalUser, on_delete=models.DO_NOTHING)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)


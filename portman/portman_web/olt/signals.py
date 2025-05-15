from django.db.models.signals import post_save
import os
from django.dispatch import receiver
from .models import FAT, OLTCabinet, Handhole, ReservedPorts
from .services.partak_web_service import PartakApi
from .services.reminders import CreateReminders
from .services.ticketer import Ticketer
from users.models import User
from datetime import datetime

PORTMAN_ENV = os.environ.get('PORTMAN_ENV', 'dev')

@receiver(post_save, sender=FAT)
def on_fat_model_saved(sender, instance, created, **kwargs):

    if created:
        Ticketer().sendFatPlanChangesTicket(instance)

@receiver(post_save, sender=OLTCabinet)
def on_cabinet_model_saved(sender, instance, created, **kwargs):
    if PORTMAN_ENV == 'prod' and not instance.is_odc:
        if not instance.crm_id and not instance.deleted_at:
            response, payload, url = PartakApi(instance).createCabinet()
            if response.get('ResponseStatus').get('ErrorCode') == 0:
                title = f"اطلاع رسانی کابینت ایجاد شده در سامانه پارتاک"
                CreateReminders.crm_cabinet_reminder(instance, title)
            else:
                CreateReminders.partak_api_error(response, payload, url)

        elif instance.deleted_at:
            title = f"اطلاع رسانی کابینت حذف شده در سامانه پارتاک"
            CreateReminders.crm_cabinet_reminder(instance, title)
    
    if created:
        Ticketer().sendCabinetPlanChangesTicket(instance)

@receiver(post_save, sender=Handhole)
def on_handhole_model_saved(sender, instance, created, **kwargs):

    if created:
        Ticketer().sendHandholePlanChangesTicket(instance)

@receiver(post_save, sender=ReservedPorts)
def on_reserved_port_model_saved(sender, instance, created, **kwargs):
    if created:
        Ticketer().sendInstallServiceTicket(instance)
    
    if instance.status == ReservedPorts.STATUS_CANCELED:
        ticket = Ticketer().findInstallServiceTicket(instance)
        if ticket:
            ticket.deleted_at = datetime.now()
            ticket.save()

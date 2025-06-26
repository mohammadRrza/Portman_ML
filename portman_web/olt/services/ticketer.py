import json
from datetime import datetime
from cartable.models import Ticket, TicketReplication, TicketType, TicketComment, TaskList, Task, Reminder
from users.models import User
from django.contrib.contenttypes.models import ContentType
from config.settings import FTTH_PROVINCE_ADMINS, FTTH_TICKET_SENDER, FTTH_INSTALL_SUPERVISORS
from olt.utility import get_current_user

class Ticketer:

    def createFtthPlanChangedTicket(self, instance, subject, body, rcvrUsernames=None, creator=None):
        creator = creator if creator else get_current_user(),
        ticket = Ticket.objects.create(
            subject=subject,
            body=body,
            type=TicketType.objects.get(name=TicketType.TYPE_FTTH_PLAN_CHANGES),
            creator=creator[0] if creator else User.objects.get(username=FTTH_TICKET_SENDER),
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id
        )

        if not rcvrUsernames:
            rcvrUsernames = FTTH_PROVINCE_ADMINS[0] # IRAN ADMIN
            if instance.city.parent.id in FTTH_PROVINCE_ADMINS:
                rcvrUsernames = FTTH_PROVINCE_ADMINS[instance.city.parent.id]

        for rcvr in rcvrUsernames:
            TicketReplication.objects.create(ticket=ticket, receiver=User.objects.get(username=rcvr))
            
        TicketReplication.objects.create(ticket=ticket, receiver=ticket.creator, read_at=datetime.now()) # a copy for creator


    def sendFatPlanChangesTicket(self, fat):
        #fat.city = fat.olt.cabinet.city
        type = 'FFAT' if fat.parent else 'FAT'
        type = 'OTB' if fat.is_otb else type
        type = 'TB' if fat.is_tb else type
        subject = f"بررسی تغییرات طرح روی {type} " + fat.name
        body = '<p>همکار گرامی</p><p>با سلام</p><br>' + \
                '<p>لطفا مراتب بررسی و تایید {0} با مشخصات زیر انجام گیرد:<p>'.format(type) +\
                '<p><b>استان/شهر:</b> {0}/{1}</p>'.format(fat.city.parent.name, fat.city.name) + \
                '<p><b>نام:</b> {0}</p>'.format(fat.name) + \
                '<br><p>با تشکر</p>'

        self.createFtthPlanChangedTicket(fat, subject, body)

    def send_disapproved_objects_ticket(self, instance, reason, receiver_usernames, disapprover):

        model_class = type(instance).__name__.lower()  # Convert class name to lowercase
        if model_class in ['building', 'cabinet', 'olt', 'fat', 'splitter', 'handhole', 'joint']:
            object_info = dict
            if model_class == 'building':
                object_info = dict(province=instance.city.parent.name, city=instance.city.name, name=instance.name, type='ساختمان'),
                
            elif model_class == 'cabinet':
                object_info = dict(province=instance.city.parent.name, city=instance.city.name, name=instance.name,
                                   type='ODC' if instance.is_odc else 'cabinet'),
            elif model_class == 'olt':
                object_info = dict(province=instance.cabinet.city.parent.name, city=instance.cabinet.city.name,
                                   name=instance.name, type='OLT')
            elif model_class == 'fat':
                fat_type = 'FFAT' if instance.parent else 'FAT'
                fat_type = 'OTB' if instance.is_otb else fat_type
                fat_type = 'TB' if instance.is_tb else fat_type
                object_info = dict(province=instance.olt.cabinet.city.parent.name, city=instance.olt.cabinet.city.name,
                                   name=instance.name, type=fat_type)
            elif model_class == 'splitter':
                object_info = dict(province=instance.FAT.olt.cabinet.city.parent.name,
                                   city=instance.FAT.olt.cabinet.city.name, name=instance.name, type='اسپلیتر')

            elif model_class == 'handhole':
                object_info = dict(province=instance.city.parent.name, city=instance.city.name,
                                   name=instance.number, type='هندهول')

            elif model_class == 'joint':
                object_info = dict(province=instance.handhole.city.parent.name, city=instance.handhole.city.name, name=instance.code, type='مفصل')

            subject = f"عدم تایید {object_info.get('type')} " + object_info.get('name')
            body = '<p>همکار گرامی</p><p>با سلام</p><br>' + \
                    '<p>به اطلاع می‌رسانیم به دلیل "{0}" {1} با مشخصات زیر توسط مسئول مربوطه تایید نگردیده است:<p>'.format(reason, object_info.get('type')) +\
                    '<p><b>استان/شهر:</b> {0}/{1}</p>'.format(object_info.get('province'), object_info.get('city')) + \
                    '<p><b>نام:</b> {0}</p>'.format(object_info.get('name')) + \
                    '<br><p>با تشکر</p>'

        else:
            instance_type = 'میکروداکت' if model_class == 'microduct' else ('پچ پنل' if model_class == 'terminal' else 'کابل')
            code = instance.code
            if model_class == 'cable':
                code = instance.generate_code()
            subject = f"عدم تایید {instance_type} "
            body = '<p>همکار گرامی</p><p>با سلام</p><br>' + \
                   '<p>به اطلاع می‌رسانیم به دلیل "{0}" {1} با مشخصات زیر توسط مسئول مربوطه تایید نگردیده است:<p>'.format(
                       reason, instance_type) + \
                   '<p><b>کد:</b> {0}</p>'.format(code) + \
                   '<br><p>با تشکر</p>'

        self.createFtthPlanChangedTicket(instance, subject, body, receiver_usernames, disapprover)

    def sendCabinetPlanChangesTicket(self, cabinet):
        type = 'ODC' if cabinet.is_odc else 'کابینت'
        subject=f"بررسی تغییرات طرح روی {type} " + cabinet.name
        body='<p>همکار گرامی</p><p>با سلام</p><br>' + \
                '<p>لطفا مراتب بررسی و تایید {0} با مشخصات زیر انجام گیرد:<p>'.format(type) +\
                '<p><b>استان/شهر:</b> {0}/{1}</p>'.format(cabinet.city.parent.name, cabinet.city.name) + \
                '<p><b>نام:</b> {0}</p>'.format(cabinet.name) + \
                '<br><p>با تشکر</p>'

        self.createFtthPlanChangedTicket(cabinet, subject, body)

    def sendHandholePlanChangesTicket(self, handhole):
        type = 'T' if handhole.is_t else 'هندهول'
        subject=f"بررسی تغییرات طرح روی {type} " + handhole.name
        body='<p>همکار گرامی</p><p>با سلام</p><br>' + \
                '<p>لطفا مراتب بررسی و تایید {0} با مشخصات زیر انجام گیرد:<p>'.format(type) +\
                '<p><b>استان/شهر:</b> {0}/{1}</p>'.format(handhole.city.parent.name, handhole.city.name) + \
                '<p><b>شماره:</b> {0}</p>'.format(handhole.number) + \
                '<br><p>با تشکر</p>'

        self.createFtthPlanChangedTicket(handhole, subject, body)

    def sendInstallServiceTicket(self, reservedPort, receiverUser=None):

        body='<p>همکار گرامی</p><p>با سلام</p><br>' + \
                '<p>لطفا مراتب طراحی، کابل‌کشی، نصب و راه اندازی سرویس مشترک با مشخصات زیر انجام گیرد:<p>' +\
                '<p><b>استان/شهر:</b> {0}/{1}</p>'.format(reservedPort.fat.city.parent.name, reservedPort.fat.city.name) + \
                '<p><b>نام مشترک:</b> {0}</p>'.format(reservedPort.customer_name) + \
                '<p><b>کد پستی:</b> {0}</p>'.format(reservedPort.postal_code) + \
                '<p><b>آدرس پستی:</b> {0}</p>'.format(reservedPort.postal_address) + \
                '<p><b>FAT:</b> {0}</p>'.format(reservedPort.fat.name) + \
                '<br><p>با تشکر</p>'

        ticket = Ticket.objects.create(
            subject="راه اندازی سرویس کاربر - {0}".format(reservedPort.customer_name),
            body=body,
            type=TicketType.objects.get(name=TicketType.TYPE_FTTH_USER_INSTALL),
            creator=User.objects.get(username=FTTH_TICKET_SENDER),
            content_type=ContentType.objects.get_for_model(reservedPort),
            object_id=reservedPort.id
        )

        taskListItems = [
            'طراحی',
            'کابل کشی',
            'نصب و راه اندازی',
            'آپلود مدارک و مستندات'
        ]

        tasklist = TaskList.objects.create(title='مراحل اجرا', created_by=ticket.creator)
        for taskItem in taskListItems:
            Task.objects.create(title=taskItem,task_list=tasklist)
        tasklist.add_to_widget(ticket=ticket)

        TicketReplication.objects.create(ticket=ticket, receiver=ticket.creator, read_at=datetime.now()) # a copy for creator
        
        if receiverUser:
            TicketReplication.objects.create(ticket=ticket, receiver=receiverUser)

        receivers = FTTH_PROVINCE_ADMINS[0] # IRAN ADMIN
        if reservedPort.fat.city.parent.id in FTTH_PROVINCE_ADMINS:
            receivers = FTTH_PROVINCE_ADMINS[reservedPort.fat.city.parent.id]
        
        supervisors = FTTH_INSTALL_SUPERVISORS[0]
        if reservedPort.fat.city.parent.id in FTTH_INSTALL_SUPERVISORS:
            supervisors = FTTH_INSTALL_SUPERVISORS[reservedPort.fat.city.parent.id]

        for sv in supervisors:
            receivers.append(sv)
        
        for r in receivers:
            #if (receiverUsername != receiverUser.username):
            TicketReplication.objects.create(ticket=ticket, receiver=User.objects.get(username=r))

    def findInstallServiceTicket(self, reservedPort):
        ticket = Ticket.objects.filter(
            content_type=ContentType.objects.get_for_model(reservedPort), 
            object_id=reservedPort.id,
            type__name=TicketType.TYPE_FTTH_USER_INSTALL,
            deleted_at__isnull=True
        ).first()
        return ticket

    def moveInstallServiceTicketToNewInstaller(self, ticket, reservedPort, oldInstaller):
        TicketReplication.objects.create(ticket=ticket, receiver=reservedPort.installer)
        if oldInstaller:
            TicketReplication.objects.filter(ticket=ticket, receiver=oldInstaller).delete()
            TicketComment.objects.create(
                body="به نصاب دیگری منتقل شد ({0})".format(oldInstaller.id),
                ticket=ticket,
                user=User.objects.get(username=FTTH_TICKET_SENDER)
            )

    def moveInstallServiceTicketToNewTechAgent(self, ticket, reservedPort, oldTechAgent):
        TicketReplication.objects.create(ticket=ticket, receiver=reservedPort.tech_agent)
        if oldTechAgent:
            TicketReplication.objects.filter(ticket=ticket, receiver=oldTechAgent).delete()
            TicketComment.objects.create(
                body="به نماینده فنی دیگری منتقل شد ({0})".format(oldTechAgent.id),
                ticket=ticket,
                user=User.objects.get(username=FTTH_TICKET_SENDER)
            )
    
    def moveInstallServiceTicketToNewCabler(self, ticket, reservedPort, oldCabler):
        TicketReplication.objects.create(ticket=ticket, receiver=reservedPort.cabler)
        if oldCabler:
            TicketReplication.objects.filter(ticket=ticket, receiver=oldCabler).delete()
            TicketComment.objects.create(
                body="به سیم‌بان دیگری منتقل شد ({0})".format(oldCabler.id),
                ticket=ticket,
                user=User.objects.get(username=FTTH_TICKET_SENDER)
            )



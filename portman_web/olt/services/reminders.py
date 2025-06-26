import json
from datetime import datetime, timedelta
from cartable.models import Reminder
from users.models import User
from rest_framework_jwt.settings import api_settings
from classes.services.mini_services import shortner_link

class CreateReminders:
    @staticmethod
    def crm_cabinet_reminder(cabinet, title):
        message = f"با عرض سلام و احترام" \
                  f"<br />" \
                  f"{title}" \
                  f"<br />" \
                  f"مشخصات کابینت:" \
                  f"<br />" \
                  f"نام: {cabinet.code}" \
                  f"<br />" \
                  f"کد: {cabinet.code}" \
                  f"<br />" \
                  f"استان: {cabinet.city.parent.name}" \
                  f"<br />" \
                  f"شهر: {cabinet.city.name}" \
                  f"<br />" \
                  f"منطقه: {cabinet.urban_district}" \
                  f"<br />" \
                  f"شناسه پارتاک: {cabinet.crm_id}"

        # crm ticket payload
        payload = json.dumps({
            "Title": title,
            "ApplicantId": "f41566a8-d041-4afb-b537-2fa6b2ca4cf2",  # sender id
            "TemplateAttributeId": "ef8c5a2e-7f98-4f63-8e48-68d14247e7ce",
            "IsRemoved": "0",
            "SaveMethod": "69e0b98b-185b-434f-be3b-d5d2f550a0ee",  # is the same for all tickets
            "Status": "28cb76a6-d999-4ee3-887c-66792287453d",  # is the same for all tickets
            "ITStaffGroupID": "E9D904BA-2B24-44EA-899C-9607117BE570",  # group id like crm or access ...
            "ITStaffId": "d0a97322-3d27-4835-b028-85ca120e6cc2",  # user id like nikpour or dehghan ...
            "SubjectList__C": "2d603057-e1b0-4db1-a406-fe76c2a32138",
            "crmSubject__C": "1a251b27-e824-4c53-936a-22c57ef870bb",
            "TicketBody": {
                "TicketBody": {
                    "Body": message,
                    "IsPublic": True

                }
            }
        })

        user = User.objects.get(email='y.nikpour@pishgaman.net')
        Reminder.objects.create(user=user, title=title, description=message, meta=payload,
                                reminder_time=datetime.now(), sending_methods='Ticket')

    @staticmethod
    def partak_api_error(response, payload, url):
        title = f"There is a problem with partak api."
        description = (f"url: {url}\r\n"
                       f"payload: {payload}\r\n"
                       f"response: {response}")
        user = User.objects.get(username='admin')
        Reminder.objects.create(user=user, title=title, description=description,
                                reminder_time=datetime.now(), sending_methods='In_App')

    def Reserved_port_notification(self, reserved_port, installer, receiver_type):

        def generateLink():
            # create token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(installer)
            payload['exp'] = datetime.utcnow() + timedelta(days=4)
            token = jwt_encode_handler(payload)
            longLink = 'https://vfttx.pishgaman.net/map.html?rp={0}&src=sms&at={1}'.format(reserved_port.id, token)
            success, shortLink, approvalCode = shortner_link(longLink=longLink, mobileNumber=installer.mobile_number)
            return shortLink, approvalCode if success else None

        def truncate_to_six_decimals(number):
            if '.' in number:
                return number[:number.index('.') + 7].ljust(number.index('.') + 7, '0')
            else:
                return number + '.000000'

        shortLink, approvalCode = generateLink()
        if receiver_type in ['installer', 'tech_agent']:
            title = 'نصب و راه اندازی کاربر'
            message = f"با سلام همکار گرامی\n\n"\
                      f"نصب و راه اندازی سرویس کاربر با مشخصات زیر به شما اختصاص یافت:\n"\
                      f"نام مشترک: {reserved_port.customer_name}\n"\
                      f"کد پستی: {reserved_port.postal_code}\n"\
                      f"آدرس: {reserved_port.postal_address}\n"\
                      f"{truncate_to_six_decimals(reserved_port.lat)},{truncate_to_six_decimals(reserved_port.lng)}\n"\
                      f"FAT: {reserved_port.fat.name}\n\n"\
                      f"برای اجرای عملیات به نرم افزار موبایل یا لینک زیر مراجعه نمایید."
        else:
            title = 'کابل‌کشی سرویس کاربر'
            message = f"با سلام همکار گرامی\n\n" \
                      f"کابل‌کشی سرویس کاربر با مشخصات زیر به شما اختصاص یافت:\n" \
                      f"نام مشترک: {reserved_port.customer_name}\n" \
                      f"کد پستی: {reserved_port.postal_code}\n" \
                      f"آدرس: {reserved_port.postal_address}\n" \
                      f"{truncate_to_six_decimals(reserved_port.lat)},{truncate_to_six_decimals(reserved_port.lng)}\n"\
                      f"FAT: {reserved_port.fat.name}\n\n" \
                      f"برای اجرای عملیات به نرم افزار موبایل یا لینک زیر مراجعه نمایید."
        
        if shortLink:
            message += "\n" + shortLink + "\n\n کد تایید: " + approvalCode

        Reminder.objects.create(user=installer, title=title, description=message,
                                reminder_time=datetime.now(), sending_methods='SMS,In_App')

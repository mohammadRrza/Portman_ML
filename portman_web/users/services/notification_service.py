from classes.mailer import Mail
import requests
import json
from django.contrib.contenttypes.models import ContentType


class Beautifier:
    def __init__(self, subject=None, message=None):
        self.subject = subject
        self.message = message

    def email_beautifier(self):
        pass


class BeautifierReminder(Beautifier):

    def email_beautifier(self):
        mail_subject = f"یادآوری {self.subject}"
        lines = self.message.strip().split("\r\n")
        if len(lines) == 1:
            message = lines[0]
        else:
            message = lines[0]
            for i, line in enumerate(lines[1:], start=1):
                line_height = "1px" if i < len(lines) - 1 else "1"
                message += f'<p style="line-height: {line_height};">{line}</p>'

        mail_message = f"""
                         <div dir="rtl" style="font-family:'Calibri', sans-serif;">
                           <h3>با سلام و احترام</h3>
                           <br />
                           <p>این ایمیل جهت یادآوری شما درباره کاری است که در سامانه پورتمن ثبت نموده‌اید.</p>

                           <div style="border-right:4px solid #007bff; padding-right:1rem; font-family:'Calibri'">
                             <h4 style="color:#007bff;">جزئیات یادآور:</h4>
                             <p><strong>موضوع:</strong> {self.subject}</p>
                             <p><strong>توضیحات:</strong> {message}</p>
                           </div>
                           <br />

                           <div dir="rtl" style="font-family:'Calibri', sans-serif;">
                             <p>سامانه پورتمن</p>
                           </div>
                         </div>
                         """

        return mail_subject, mail_message


class Notification:
    def __init__(self, receivers, message, channels, subject, content_type, object_id, sender=None, metadata=None):
        from ..models import User
        self.receivers = receivers
        self.message = message
        self.channels = channels
        self.subject = subject
        self.content_type = content_type
        self.object_id = object_id
        self.sender = sender if sender else User.objects.get(username='admin')
        self.send_type = None
        self.metadata = metadata
        self.response = None


class NotificationChannel:

    def send(self):
        pass

    def save_notif_log(self, notification: Notification):
        from ..models import NotificationLog
        for receiver in notification.receivers:
            NotificationLog.objects.create(message=notification.message,
                                           sender=notification.sender,
                                           receiver=receiver,
                                           send_type=notification.send_type,
                                           response=notification.response,
                                           content_type=notification.content_type,
                                           object_id=notification.object_id)


class EmailNotificationChannel(NotificationChannel):
    def __init__(self, text_type: str):
        self.text_type = text_type

    def send(self, notification: Notification):
        from cartable.models import Reminder
        mail_info = Mail()
        mail_info.from_addr = 'oss-notification@pishgaman.net'
        emails_address = ', '.join([receiver.email for receiver in notification.receivers])
        mail_info.to_addr = emails_address
        mail_info.msg_subject = notification.subject
        mail_info.msg_body = notification.message
        mail_info.text_type = self.text_type
        structure = None
        if notification.metadata:
            metadata = json.loads(notification.metadata.replace("'", '"'))
            if metadata.get('cc'):
                mail_info.cc = ', '.join([cc for cc in metadata.get('cc')])
            structure = metadata.get('structure') if metadata.get('structure') else None
        if notification.content_type == ContentType.objects.get_for_model(Reminder) and not structure:
            mail_info.msg_subject,  mail_info.msg_body = BeautifierReminder(subject=notification.subject,
                                                                            message=notification.message).email_beautifier()

        Mail.Send_Mail(mail_info)
        notification.send_type = 'email'
        self.save_notif_log(notification)

        return f"Sending email notification to {emails_address}: {notification.message}"

    def beautifying_selector(self, content_type):
        from cartable.models import Reminder
        if content_type == ContentType.objects.get_for_model(Reminder):
            return


class SMSNotificationChannel(NotificationChannel):

    def __init__(self):
        pass

    def send(self, notification: Notification):
        login_url = 'http://api.pishgaman.net/gateway/token'
        response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                    "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                                                    "appid": "57"})
        for receiver in notification.receivers:
            token = response.json()
            send_message_url = "http://api.pishgaman.net/gateway/notifications/sms"

            payload = json.dumps({
                "destination": f"{receiver.mobile_number}",
                "body": f"{notification.message}",
                "title": f"{notification.subject}",
                "appId": 1
            })
            headers = {
                'Authorization': "Bearer " + token['Result'],
                'appid': '57',
                'Content-Type': 'application/json'
            }

            requests.request("POST", send_message_url, headers=headers, data=payload)

        return 'Message sent.'


class InAppNotificationChannel(NotificationChannel):
    def __init__(self):
        pass

    def send(self, notification: Notification):
        notification.send_type = 'in_app'
        self.save_notif_log(notification)


class TicketNotificationChannel(NotificationChannel):
    def __init__(self):
        pass

    def _access_token(self):
        login_url = 'https://ticketing.pishgaman.net/api/v1/Token/GetToken'
        login_data = str(dict(Username="software", Password="6CJ796MJ8oB",
                              secret="0871EB460075E047A708D830D2F80D10CCBCB30B"))
        response = requests.post(login_url, data=login_data, headers={
            'Content-Type': 'application/json'
        })
        response_json = response.json()
        return response_json['ResultData']['access_token']

    def send(self, notification: Notification):
        url = "https://ticketing.pishgaman.net/api/v1/Ticket"
        token = self._access_token()

        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=notification.metadata)
        notification.send_type = 'ticket'
        notification.response = response.text
        self.save_notif_log(notification)

        return response.text


class NotificationService:
    def send(self, notification: Notification):
        for channel in notification.channels:
            channel.send(notification)

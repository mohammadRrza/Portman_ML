import requests
import sys
import os
from users.models import NotificationLog


def save_notif_log(sender, receiver, message, send_type):
    try:
        NotificationLog.objects.create(message=message, sender=sender, receiver=receiver, send_type=send_type)
        return True
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print({'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)})
    return False


def send_message(sender, receivers, message, send_type):
    try:
        send_status = False
        login_url = 'http://api.pishgaman.net/gateway/token'
        response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                    "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                                                    "appid": "57"})
        response_json = response.json()
        for receiver in receivers:
            send_message_url = f"http://api.pishgaman.net/gateway/api/sms/send?destination={receiver.mobile_number}&body={message}"
            send_message_response = requests.get(send_message_url,
                                                 headers={"Content-Type": "application/json",
                                                          "Authorization": "Bearer " + response_json['Result'],
                                                          "appid": "57"})
            send_message_response_json = send_message_response.json()
            if send_message_response_json.get('OperationResultCode') == 200:
                send_status = True
                save_notif_log(sender, receiver, message, send_type)

        if send_status:
            return True
        else:
            return False

    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        return {'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)}
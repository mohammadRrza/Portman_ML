import requests
from dslam.models import DSLAM
from dslam import utility
from rest_framework import status
import re
from datetime import datetime
import sys

class GetDataFromIBS:
    def __init__(self):
        pass

    def get_mac_address_from_ibs(self, username, from_date, from_time, to_date, to_time):
        try:
            login_url = 'http://api.pishgaman.net/gateway/token'
            login_data = "{'Username':'oss','Password':'74e#$pRe;F'}"
            response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                        "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                                                        "appid": "57"})
            response_json = response.json()
            getuserinfo_url = "http://api.pishgaman.net/gateway/accounting/mac/by/username/"
            payload = {
                "fromdate": from_date,
                "fromtime": from_time,
                "todate": to_date,
                "totime": to_time,
                "username": username
            }
            userinfo_response = requests.post(getuserinfo_url,
                                              headers={"Content-Type": "application/json",
                                                       "Authorization": "Bearer " + response_json['Result'],
                                                       "appid": "57"}, json=payload)

            userinfo_response_json = userinfo_response.json()
            result = userinfo_response_json.get("Result").get("Result")
            print(result, "SSSsS", userinfo_response.headers, getuserinfo_url, from_date)
            return True, result.get("MacId")
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})
            return False, ""

    def get_user_info_from_ibs(self, username):
        try:
            partak_url = 'https://my.pishgaman.net/api/pte/getCustomerNetUsername?Adsltel=' + username
            partak_response = requests.get(partak_url).json()
            panel_username = partak_response['AcoountInfo']['username']
            login_url = 'http://api.pishgaman.net/gateway/token'
            login_data = "{'Username':'oss','Password':'74e#$pRe;F'}"
            response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                        "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                                                        "appid": "57"})
            response_json = response.json()
            getuserinfo_url = 'http://api.pishgaman.net/gateway/api/ibs/getUserInfo?username=' + panel_username
            userinfo_response = requests.get(getuserinfo_url,
                                              headers={"Content-Type": "application/json",
                                                       "Authorization": "Bearer " + response_json['Result'],
                                                       "appid": "57"})

            userinfo_response_json = userinfo_response.json()
            for key in userinfo_response_json['Result']['result']:
                if not userinfo_response_json['Result']['result'][key]['online_status']:
                    return dict(mac='', info=None, is_online=False, error='User is offline.', status=status.HTTP_404_NOT_FOUND)

            if userinfo_response_json.get('error', None) and 'does not exists' in userinfo_response_json.get('error', None):
                return dict(
                    mac='',
                    is_online=False, 
                    error="Error" + str(userinfo_response_json['error']),
                    info=None,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            for value in userinfo_response_json['Result']['result']:
                info = userinfo_response_json['Result']['result'][value]
                isOnline = info.get('online_status')
                mac = isOnline and info.get('internet_onlines')[0][7]
                return dict(
                    mac=info.get('attrs').get('limit_mac', mac),
                    is_online=isOnline,
                    info=info,
                    error=None,
                    status=status.HTTP_200_OK
                )
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})
            return {'result': str(ex), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

import json
import requests
import jwt
from datetime import datetime


class PishgamanGeteway:

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PishgamanGeteway, cls).__new__(cls)
            login_url = "http://api.pishgaman.net/gateway/token"
            headers = {"Content-Type": "application/json",
                       "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                       "appid": "57"}
            response = requests.get(login_url, headers=headers)
            cls.login_parameters = response.json()

        return cls.instance

    def __init__(self):
        self.check_token(self.login_parameters)

    def login(self):
        login_url = "http://api.pishgaman.net/gateway/token"
        headers = {"Content-Type": "application/json",
                   "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
                   "appid": "57"}
        try:
            response = requests.get(login_url, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            print(response_json)
            return response_json
        except requests.exceptions.RequestException as e:
            raise Exception("Failed to retrieve API token.") from e

    def check_token(self, login_parameter):
        token = login_parameter.get('Result')
        decoded = jwt.decode(token.encode('utf-8'), verify=False)
        expire_date = datetime.fromtimestamp(decoded['exp'])
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_now = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
        if date_now > expire_date:
            self.login_parameters = self.login()

    def config_acs(self, Adsltel, serial_number):
        url = "http://api.pishgaman.net/gateway/api/crm/modem/serial"
        token = self.login_parameters.get('Result')

        payload = {'Adsltel': Adsltel,
                   'SerialNumber': serial_number}
        headers = {
            'AppId': '57',
            'Authorization': f'Bearer {token}'
        }
        response = requests.request("PATCH", url, headers=headers, data=payload)
        return response.json()


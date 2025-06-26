import time
from datetime import datetime
import jwt

import requests
import os, sys
from .data_locations_logging import LocationsActionsLogging


class LocationServicesV2(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LocationServicesV2, cls).__new__(cls)
            cls.ip = '172.28.241.58'
            cls.port = '82'
            login_url = "http://api.pishgaman.net/gateway/token"
            login_data = "{'Username':'oss','Password':'74e#$pRe;F'}"
            response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                        "Authorization": "Basic b3NzLXBvcnRtYW4tZGV2Oj00I19aTl4rZ0orMXkvUCxPNEJmLDJtVlp4ZD9xRUkj",
                                                        "Appid": "26"})
            cls.login_parameters = response.json()

        return cls.instance

    def __init__(self):
        self.check_token(self.login_parameters)

    def check_token(self, login_parameter):
        try:
            token = login_parameter.get('Result')
            decoded = jwt.decode(token.encode('utf-8'), verify=False)
            expire_date = datetime.fromtimestamp(decoded['exp'])
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_now = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")

            if date_now > expire_date:
                login_url = "http://api.pishgaman.net/gateway/token"
                response = requests.get(login_url, headers={"Content-Type": "application/json",
                                                            "Authorization": "Basic b3NzLXBvcnRtYW4tZGV2Oj00I19aTl4rZ0orMXkvUCxPNEJmLDJtVlp4ZD9xRUkj",
                                                            "Appid": "26"})
                self.login_parameters = response.json()
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def get_data_location(self, params):
        try:
            url = f"http://api.pishgaman.net/gateway/DataLocation/search"
            print(str(params))
            ip = params.get('ip', None)
            str_params = '{' + f'"PageNumber": {params.get("PageNumber")}, "PageSize": {params.get("PageSize")},' + \
                         '"DataLocation": 0''}'
            if ip:
                str_params = '{' + f'"PageNumber": {params.get("PageNumber")}, "PageSize": {params.get("PageSize")},'\
                             + f'"IP": "{params.get("ip")}", "DataLocation": 0' + '}'
            print(str(str_params))
            api_token = self.login_parameters.get('Result')
            response = requests.get(url, data=str_params, headers={"Content-Type": "application/json",
                                                                   "Authorization": f"Bearer {api_token}",
                                                                   "Appid": "26"})
            response_json = response.json()
            return response_json
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def create_data_location(self, params):
        try:
            log_params = dict(username=params.get('username'), action='create', new_ip=params.get('IP'))
            url = f"http://api.pishgaman.net/gateway/DataLocation"
            params_str = f"{str(params)}".replace("'", '"')
            api_token = self.login_parameters.get('Result')
            response = requests.post(url, data=params_str, headers={"Content-Type": "application/json",
                                                                    "Authorization": f"Bearer {api_token}",
                                                                    "Appid": "26"})
            if response.status_code == 201:
                result = f"new data with parameters ip: {params.get('ip')}, data_location: {params.get('DataLocation')}," \
                         f"info: {params.get('info')} successfully created."
                log_params['result'] = result
                log_params['status'] = 'Successful'
                LocationsActionsLogging(log_params)
                return "Successfully created."
            else:
                result = f"Oops!!! An error occurred. Error is {response.json()} " \
                         f"new data with parameters ip: {params.get('ip')}, data_location: {params.get('DataLocation')}," \
                         f"info: {params.get('info')} encountered an error."
                log_params['result'] = result
                log_params['status'] = 'Failed'
                LocationsActionsLogging(log_params)
                return response.json()
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def delete_data_location(self, params):
        log_params = dict(username=params.get('username'), action='delete', new_ip=params.get('ip'))
        url = f"http://api.pishgaman.net/gateway/DataLocation?ip={params.get('ip')}"
        api_token = self.login_parameters.get('Result')
        response = requests.delete(url, headers={"Content-Type": "application/json",
                                                 "Authorization": f"Bearer {api_token}",
                                                 "Appid": "26"})
        if response.status_code == 200:
            result = f"Location data with ip: {params.get('ip')} successfully deleted"
            log_params['result'] = result
            log_params['status'] = 'Successful'
            LocationsActionsLogging(log_params)
            return "Successfully deleted."
        else:
            result = f"Oops!!! An error occurred. Error is {response.json()}"
            log_params['result'] = result
            log_params['status'] = 'Failed'
            LocationsActionsLogging(log_params)
            return response.json()

    def update_data_location(self, params):
        try:
            url = f"http://api.pishgaman.net/gateway/DataLocation"
            api_token = self.login_parameters.get('Result')
            params = f"{str(params)}".replace("'", '"')
            print(params)
            response = requests.put(url, data=params, headers={"Content-Type": "application/json",
                                                               "Authorization": f"Bearer {api_token}",
                                                               "Appid": "26"})
            if response.status_code == 200:
                return dict(result="Successfully edited.", status=200)
            else:
                return dict(result=response.json(), status=500)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def get_static_locations(self):
        try:
            url = f"http://api.pishgaman.net/gateway/DataLocation"
            api_token = self.login_parameters.get('Result')
            response = requests.get(url, headers={"Content-Type": "application/json",
                                                               "Authorization": f"Bearer {api_token}",
                                                               "Appid": "26"})
            response_json = response.json()
            return response_json
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})


import time
from datetime import datetime

import requests
import os, sys
from .data_locations_logging import LocationsActionsLogging

class LocationServices(object):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LocationServices, cls).__new__(cls)
            cls.ip = '172.28.241.58'
            cls.port = '82'
            login_url = f"http://{cls.ip}:{cls.port}/api/Authentication/Login"
            login_data = '{"username": "oss","password": "&o5qbGI79W@"}'
            response = requests.post(login_url, data=login_data, headers={"Content-Type": "application/json"})
            cls.login_parameters = response.json()

        return cls.instance

    def __init__(self):
        self.check_token(self.login_parameters)

    def check_token(self, login_parameter):
        try:
            expire_date = login_parameter.get('expireDate')
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expire_date = datetime.strptime(expire_date, '%Y-%m-%dT%H:%M:%S%z').strftime("%Y-%m-%d %H:%M:%S")
            expire_date = datetime.strptime(expire_date, "%Y-%m-%d %H:%M:%S")
            date_now = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")

            if date_now > expire_date:
                login_url = f"http://{self.ip}:{self.port}/api/Authentication/Login"
                login_data = '{"username": "oss","password": "&o5qbGI79W@"}'
                response = requests.post(login_url, data=login_data, headers={"Content-Type": "application/json"})
                self.login_parameters = response.json()
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def get_data_location(self, params):
        try:
            url = f"http://{self.ip}:{self.port}/api/DataLocation?"
            params = params
            page_number = params.get('page_number', None)
            page_size = params.get('page_size', None)
            ip = params.get('ip', None)
            data_location = params.get('data_location', None)
            if page_number:
                url += f"pageNumber={page_number}&"
            if page_size:
                url += f"pageSize={page_size}&"
            if ip:
                url += f"ip={ip}&"
            if data_location:
                url += f"dataLocation={data_location}"

            api_token = self.login_parameters.get('token')
            response = requests.get(url, headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {api_token}"})
            response_json = response.json()
            return response_json
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def create_data_location(self, params):
        try:
            log_params = dict(username=params.get('username'), action='create', new_ip=params.get('ip'))
            url = f"http://{self.ip}:{self.port}/api/DataLocation"
            params_str = f"{str(params)}".replace("'", '"')
            api_token = self.login_parameters.get('token')
            response = requests.post(url, data=params_str, headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {api_token}"})
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
        url = f"http://{self.ip}:{self.port}/api/DataLocation?id={params.get('id')}"
        api_token = self.login_parameters.get('token')
        response = requests.delete(url, headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {api_token}"})
        if response.status_code == 204:
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
            url = f"http://{self.ip}:{self.port}/api/DataLocation"
            new_data = params.get('new_data')
            old_data = params.get('old_data')
            log_params = dict(username=params.get('username'), action='edit', new_ip=new_data.get('ip'),
                              old_ip=old_data.get('ip'))
            request_data = params.get('new_data')
            request_data['id'] = params.get('id')
            request_data = f"{str(request_data)}".replace("'", '"')
            api_token = self.login_parameters.get('token')
            response = requests.put(url, data=request_data, headers={"Content-Type": "application/json",
                                                                      "Authorization": f"Bearer {api_token}"})
            if response.status_code == 204:
                log_params['status'] = 'Successful'
                result = f"Location data with information (ip: {old_data.get('ip')}, dataLocation:" \
                         f" {old_data.get('dataLocation')}, info: {old_data.get('info')}) edited to" \
                         f"(ip: {new_data.get('ip')}, dataLocation: {new_data.get('dataLocation')}, info: " \
                         f"{new_data.get('info')})."
                log_params['result'] = result
                LocationsActionsLogging(log_params)
                return dict(result="Successfully edited.", status=200)
            else:
                log_params['status'] = 'Failed'
                result = f"Oops!!! An error occurred. Error is {response.json()} " \
                         f"Location data with information (ip: {old_data.get('ip')}, dataLocation:" \
                         f" {old_data.get('dataLocation')}, info: {old_data.get('info')}) can't edite to" \
                         f"(ip: {new_data.get('ip')}, dataLocation: {new_data.get('dataLocation')}, info: " \
                         f"{new_data.get('info')})."
                log_params['result'] = result
                LocationsActionsLogging(log_params)
                return dict(result=response.json(), status=500)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

    def get_static_locations(self):
        try:
            url = f"http://{self.ip}:{self.port}/api/DataLocation/GetStaticLocations"
            api_token = self.login_parameters.get('token')
            response = requests.get(url, headers={"Content-Type": "application/json",
                                                  "Authorization": f"Bearer {api_token}"})
            response_json = response.json()
            return response_json
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return ({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})

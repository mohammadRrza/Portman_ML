import os
import sys
import telnetlib
import time
from .command_base import BaseCommand
import re


class SwitchPortShow(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.device_ip = params.get('device_ip')
        self.request_from_ui = params.get('request_from_ui')

    @property
    def HOST(self):
        return self.__HOST

    @HOST.setter
    def HOST(self, value):
        self.__HOST = value

    @property
    def port_name(self):
        return self.__port_name

    @port_name.setter
    def port_name(self, value):
        self.__port_name = self.__clear_port_name(value)

    @property
    def telnet_username(self):
        return self.__telnet_username

    @telnet_username.setter
    def telnet_username(self, value):
        self.__telnet_username = value

    @property
    def telnet_password(self):
        return self.__telnet_password

    @telnet_password.setter
    def telnet_password(self, value):
        self.__telnet_password = value

    def __clear_port_name(self, port_name):
        pattern = r'\d+(\s)?-(\s)?\d+'
        st = re.search(pattern, port_name, re.M | re.DOTALL)
        return st.group()

    retry = 1

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            tn.read_until(b"Password:")
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err1 = tn.read_until(b'Communications Corp.', 1)
            if "Password:" in str(err1):
                return dict(resutl="Telnet Username or Password is wrong! Please contact with core-access department.", status=500)
            tn.write(b"switch port show\r\n")
            tn.write(b"end*\r\n")
            result = tn.read_until(b'end*')
            if self.request_from_ui:
                return dict(result=result.decode('utf-8'), status=200)
            result = str(result).split('\\r\\n')
            result = [val for val in result if re.search(r'--{3,}|\s{3,}', val)]
            tn.write(b"exit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            print('********************************')
            print(result)
            print('********************************')
            return dict(result=result, status=200)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno)))
            print(e)
            self.retry += 1
            if self.retry < 3:
                return self.run_command()

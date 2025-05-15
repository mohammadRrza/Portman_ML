import os
import telnetlib
import sys
import time
from socket import error as socket_error
import re
from .command_base import BaseCommand


# from easysnmp import Session

class ProfileADSLShow(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__params = params
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
            if tn.read_until(b'>>User name:'):
                tn.write((self.__telnet_username + "\n").encode('utf-8'))
            if tn.read_until(b'>>User password:'):
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            result = tn.read_until(b">", 0.5)
            output = str(result)
            while '>' not in str(result):
                result = tn.read_until(b">", 1)
                output += str(result)
                tn.write(b"\r\n")
            tn.write("enable\r\n".encode('utf-8'))
            tn.write("config\r\n".encode('utf-8'))
            tn.read_until(b"(config)#")
            tn.write(b"display adsl line-profile\r\n")
            tn.write(b"\r\n")
            result = tn.read_until(b"(config)#", 0.1)
            output = result.decode('utf-8')
            while '(config)#' not in str(result):
                tn.write(b"\r\n")
                result = tn.read_until(b"(config)#", 0.1)
                output += str(result.decode('utf-8'))

            if self.request_from_ui:
                output = output.replace('\\r\\n', '\r\n')
                return {"result": output, "status": 200}

            lines = re.split("\r\n", output)
            profiles = [item.strip() for item in lines if re.search(r'^\s+\d+\s+', item)]

            profile_list = []
            for item in profiles:
                if len(item) > 5:
                    profile_list.append(item.split()[1])



            tn.write(b"quit\r\n")
            tn.write(b"quit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            return {"result": profile_list, "status": 200}
        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno)))
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

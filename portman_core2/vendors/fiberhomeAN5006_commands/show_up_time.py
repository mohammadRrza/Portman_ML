import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowUpTime(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.device_ip = params.get('device_ip')
        self.request_from_ui = params.get('request_from_ui')

    @property
    def HOST(self):
        return self.__HOST

    @HOST.setter
    def HOST(self, value):
        self.__HOST = value

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

    retry = 1

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err1 = tn.read_until(b"#", 0.2)
            if "Login Failed." in str(err1):
                return dict(result="Telnet Username or Password is wrong! Please contact with core-access department.", status=500)
            tn.write(b"cd service\r\n")
            tn.write("telnet Slot {0}\r\n\r\n".format(self.port_conditions['slot_number']).encode('utf-8'))
            fiber5006_1=tn.read_until(b"Login", 0.2)
            fiber5006_2=tn.read_until(b"xDSL", 0.2)

            time.sleep(0.1)
            if "Login" in str(fiber5006_1):
                print('Login')
                tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
                if tn.read_until(b"User>"):
                        tn.write(b"enable\r\n")
                        tn.write((self.__telnet_password + "\r\n").encode('utf-8'))

            tn.write(b"cd dsp\r\n")
            tn.write("show port status {0}\r\n\r\n".format(self.port_conditions['port_number']).encode('utf-8'))
            time.sleep(1)
            tn.write("end\r\n".encode('utf-8'))
            result = tn.read_until(b"end")
            if "unreached" in str(result):
                return dict(result="The Card number maybe unavailable or does not exist.", status=500)
            if "Invalid slot number!" in str(result):
                return dict(result="Card number is out of range.", status=500)
            if "status:" not in str(result):
                return dict(result="Port number is out of range.", status=500)
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.close()
            result = str(result).split("\\r\\n")
            result = [item for item in result if re.search('up time|Line Distance', item)]
            up_time = result[0].split(':')[1].strip()
            if len(result) == 2:
                line_distance = result[1].split(':')[1].strip()
                result = f"card/port = {self.port_conditions['slot_number']}/{self.port_conditions['port_number']} | " \
                         f"uptime = {up_time}, line_distance = {line_distance}"
                return dict(result=result, status=200)
            else:
                return dict(result=f"card/port = {self.port_conditions['slot_number']}/{self.port_conditions['port_number']} | " \
                         f"uptime = {up_time}", status=200)



        except (EOFError, socket_error) as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno) + '//1'))
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno) + '//2'))
            print(e)
            print(e)
            return str(e)

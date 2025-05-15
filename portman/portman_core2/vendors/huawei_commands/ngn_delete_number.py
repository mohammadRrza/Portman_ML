import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class NGNDeleteNumber(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.device_ip = params.get('device_ip')
        self.command_str = "sippstnuser del 0/{0}/{1}".format(self.port_conditions['slot_number'], self.port_conditions['port_number'])


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

    def clean_output(self, result):
        try :
            start = result.find(self.command_str)
            return dict(result=result[start:], status=200)
        except:
            pass

        return dict(result=result, status=500)

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            if tn.read_until(b'>>User name:'):
                tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            if tn.read_until(b'>>User password:'):
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(b"eenable\r\n")
            tn.write(b"enable\r\n")
            tn.write(b"config\r\n")
            tn.write(b"esl user\r\n")
            tn.write((self.command_str + "\r\n").encode('utf-8'))
            time.sleep(0.5)
            tn.write(b"y\r\n")
            tn.write(b"end\r\n")
            result = tn.read_until(b'end')
            tn.write(b"quit\r\n")
            tn.write(b"y\r\n")
            tn.close()

            if 'is not configured with user data' in str(result):
                return dict(result="Failure: Port 0/{0}/{1} is not configured with user data".format(self.port_conditions['slot_number'], self.port_conditions['port_number']), status=500)
            if 'is not confirmed' in str(result):
                return dict(result="Failure: Board 0/{0} is not confirmed".format(self.port_conditions['slot_number']), status=500)
            
            return self.clean_output(result.decode('utf-8'))
        except (EOFError, socket_error) as e:
            print('============socket_error==========')
            print(e)
            print('============socket_error==========')
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('============Exception==========')
            print(str(e)+"///"+str(exc_tb.tb_lineno))
            print('============Exception==========')
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class AssignNumberToUser(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.device_ip = params.get('device_ip')
        self.__phone_number = self.port_conditions['ngn_phon_number']
        self.__sip_password = self.port_conditions['ngn_password']
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
                tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            if tn.read_until(b'>>User password:'):
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b"eenable\r\n")
            tn.write(b"enable\r\n")
            tn.write(b"config\r\n")
            tn.write(b"esl user\r\n")
            tn.write(("sippstnuser add 0/{}/{} 0 telno {}\r\n".format(self.port_conditions['slot_number'], self.port_conditions['port_number'], self.__phone_number)).encode('utf-8'))
            tn.write(("sippstnuser attribute set 0/{}/{} dc-time 80\r\n\r\n\r\n\r\n".format(self.port_conditions['slot_number'], self.port_conditions['port_number'])).encode('utf-8'))
            time.sleep(2)
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(("sippstnuser rightflag set 0/{}/{}  telno {} cw disable\r\n".format(self.port_conditions['slot_number'], self.port_conditions['port_number'], self.__phone_number)).encode('utf-8'))
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(("sippstnuser auth set 0/{}/{} telno {} password-mode password\r\n".format(self.port_conditions['slot_number'], self.port_conditions['port_number'], self.__phone_number)).encode('utf-8'))
            # if tn.read_until(b'User Name(<=64 characters, "-" indicates deletion):'):
            tn.write((self.__phone_number+"\r\n").encode('utf-8'))
            if tn.read_until(b'User Password(<=64 characters, "-" indicates deletion):', 2):
                tn.write((self.__sip_password+"\r\n").encode('utf-8'))
            tn.write(("display sippstnuser 0/{}\r\n".format(self.port_conditions['slot_number'])).encode('utf-8'))
            tn.write(b"end2\r\n")
            result = tn.read_until(b'end2', 2)
            tn.write(b"quit\r\n")
            tn.write(b"y\r\n")
            tn.close()

            if 'is not configured with user data' in str(result):
                return dict(result="Failure: Port 0/{0}/{1} is not configured with user data".format(self.port_conditions['slot_number'], self.port_conditions['port_number']), status=500)
            if 'is not confirmed' in str(result):
                return dict(result="Failure: Board 0/{0} is not confirmed".format(self.port_conditions['slot_number']), status=500)
            return dict(result=result.decode('utf-8'), status=200)
        except (EOFError, socket_error) as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('============Exception==========')
            print(str(e)+"///"+str(exc_tb.tb_lineno))
            print('============Exception==========')
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

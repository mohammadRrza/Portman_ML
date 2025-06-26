import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re
from .port_enable import PortEnable
from .port_disable import PortDisable

class PortReset(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.device_ip = params.get('device_ip')
        self.enablePort = PortEnable(params)
        self.disablePort = PortDisable(params)

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

    def init_commands(self):
        self.disablePort.HOST = self.__HOST
        self.disablePort.telnet_username = self.__telnet_username
        self.disablePort.telnet_password = self.__telnet_password

        self.enablePort.HOST = self.__HOST
        self.enablePort.telnet_username = self.__telnet_username
        self.enablePort.telnet_password = self.__telnet_password

    retry = 1
    def run_command(self):
        try:
            self.init_commands()
            self.disablePort.run_command()
            time.sleep(1)
            self.enablePort.run_command()
            print('******************************************')
            print(("port reset {0}".format(self.port_conditions)))
            print('******************************************')
            return dict(result="Port reset successfully.", port_indexes=self.port_conditions, status=200)
        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 3:
                return self.run_command()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno)))
            print(e)
            self.retry += 1
            if self.retry < 3:
                return self.run_command()

import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re

class LcmanShowSlot(BaseCommand):
    def __init__(self, params):
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
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            time.sleep(1)
            tn.read_until(b"Password:")
            tn.write("lcman show {0}\r\n\r\n".format(self.port_conditions['slot_number']).encode('utf-8'))
            time.sleep(1)
            tn.write(b"end*\r\n")
            result = tn.read_until(b'end*')
            tn.write(b"exit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            start_point = result.find(b'slot')
            end_point = result.rfind(b'\r\n\r\n')
            if self.request_from_ui:
                return dict(result=result.decode('utf-8'), status=200)
            result = result[start_point:end_point]

            print('********************************')
            print(result)
            print('********************************')
            return {"result": result, "status": 200}

        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
        except Exception as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

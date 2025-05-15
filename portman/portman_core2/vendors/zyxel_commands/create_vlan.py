import telnetlib
import time
from .command_base import BaseCommand
import re


class CreateVlan(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__vlan_id = params.get('vlan_id', '1')
        self.__vlan_name = params.get('vlan_name', None)
        self.device_ip = params.get('device_ip')

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
            tn.read_until(b'Password:')
            tn.write("vlan set {0} all fix tag\r\n\r\n".format(
                self.__vlan_id
            ).encode('utf-8'))
            time.sleep(1)
            if self.__vlan_name:
                tn.write("vlan name {0} {1}\r\n\r\n".format(
                    self.__vlan_id,
                    self.__vlan_name
                ).encode('utf-8'))
                time.sleep(1)
            tn.write(b"end*\r\n")
            result = tn.read_until(b'end*')
            tn.write(b"exit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            if 'example' in str(result):
                print('************************************')
                print(("error: {0} vlan created".format(self.__vlan_id)))
                print('************************************')
                return {"result": "error: {0} vlan created".format(self.__vlan_id), "status": 500}
            print('************************************')
            print(("{0} vlan created".format(self.__vlan_id)))
            print('************************************')
            return {"result": "{0} vlan created".format(self.__vlan_id), "status": 200}
        except Exception as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

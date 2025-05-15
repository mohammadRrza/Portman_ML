import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowPortByMac(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__port_name = None
        self.__mac = params.get('mac')
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

    def __clear_port_name(self,port_name):
        pattern = r'\d+(\s)?-(\s)?\d+'
        st = re.search(pattern,port_name,re.M|re.DOTALL)
        return st.group()

    retry = 1
    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            if tn.read_until(b'>>User name:'):
                tn.write((self.__telnet_username + "\n").encode('utf-8'))
            if tn.read_until(b'>>User password:'):
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b'q\r\n')
            tn.write(b"end\r\n")
            err = tn.read_until(b'end', 2)
            if 'invalid' in str(err):
                return dict(result='Telnet Username or Password is wrong! Please contact with core-access department.',
                            status=500)
            if 'Reenter times' in str(err):
                return dict(result='The device is busy right now. Please try a few moments later.',
                            status=500)

            if ':' in self.__mac:
                self.__mac = re.sub(':', '', self.__mac)
                self.__mac = self.__mac[:4] + '-' + self.__mac[4:8] + '-' + self.__mac[8:]

            tn.write(b"\r\n")
            tn.write(b"enable\r\n")
            tn.write(b"config\r\n")
            tn.read_until(b"(config)#", 2)
            tn.write("display mac-address all\r\n".encode('utf-8'))
            for i in range(60):
                tn.write(b'\r\n')
            tn.write(b'finish\r\n')
            output =tn.read_until(b"finish", 5)
            output = str(output)
            if self.__mac in output:
                output = output.split("\\r\\n")
                for item in output:
                    if self.__mac in item:
                        vlan_id = item.split()[-1]
                        if vlan_id == 'TLS':
                            return dict(result=f"The mac {self.__mac} in vlan TLS", status=500)
                        tn.write("display mac-address vlan {0}\r\n".format(vlan_id).encode('utf-8'))
                        time.sleep(0.5)
                        for i in range(60):
                            tn.write(b'\r\n')
                        tn.write(b'finish\r\n')
                        result = tn.read_until(b'finish', 3)
                        result = str(result).split("\\r\\n")
                        for value in result:
                            if self.__mac in value:
                                card = value.split('/')[-2].strip()
                                port = value.split('/')[-1].split()[0].strip()
                                return dict(result=f"card: {card}, port: {port}", status=200)

            else:
                return dict(result=f"MAC Address: {self.__mac} does not exist.", status=500)

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

import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class RemoveFromVlan(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__port_indexes = params.get('port_indexes')
        self.__vpi = params.get('vpi', '0')
        self.__vci = params.get('vci', '35')
        self.__profile = params.get('profile', 'DEFVAL')
        self.__mux = params.get('mux', 'llc')
        self.__vlan_id = params.get('vlan_id', '1')
        self.__vlan_name = params.get('vlan_name', '1')
        self.__priority = params.get('priority', '0')
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
            # port pvc set <slot-port-vpi/vci> <profile> <mux> <pvlan_id> <priority>
            tn.write("vlan set {0} all fix tag\r\n\r\n".format(
                self.__vlan_id,
            ).encode('utf-8'))
            time.sleep(1)
            if self.__vlan_name:
                tn.write("vlan name {0} {1}\r\n\r\n".format(
                    self.__vlan_id,
                    self.__vlan_name
                ).encode('utf-8'))
                time.sleep(1)
            for port_item in self.__port_indexes:
                tn.write("port pvc delete {0}-{1}-{2}/{3}\r\n\r\n".format(
                    port_item['slot_number'], port_item['port_number'],
                    self.__vpi,
                    self.__vci).encode('utf-8'))
                time.sleep(1)
            tn.write(b"end*\r\n")
            result = tn.read_until(b'end*')
            tn.write(b"exit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            if 'example' in str(result):
                return {"result": "The delete from card/port {0} gives error".format(self.__port_indexes),
                        "port_indexes": self.__port_indexes, "status": 500}
            return dict(result="deleted from card/port{0}".format(self.__port_indexes),
                        port_indexes=self.__port_indexes, status=200)
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
            else:
                print(("error : delete from card/port {0}".format(self.__port_indexes)))
                return {"result": "delete from card/port {1}".format(self.__port_indexes)}

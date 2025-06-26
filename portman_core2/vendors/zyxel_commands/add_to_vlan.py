import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class AddToVlan(BaseCommand):
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
            time.sleep(1)
            if self.__vlan_name:
                tn.write("vlan name {0} {1}\r\n\r\n".format(
                    self.__vlan_id,
                    self.__vlan_name
                ).encode('utf-8'))
                time.sleep(1)
            for port_item in self.__port_indexes:
                tn.write("port pvc show {0}-{1}\r\n".format(port_item['slot_number'], port_item['port_number']).encode('utf-8'))
                tn.write(b'end*\r\n')
                result = tn.read_until(b'end*', 0.3)
                result = str(result).split('\\r\\n')
                result = [item for item in result if re.search(r'\d+-\d+-\d+', item)]
                for item in result:
                    old_vpi = item.split('/')[0].split('-')[-1]
                    old_vci = item.split('/')[1].split()[0]
                    tn.write("port pvc delete {0}-{1}-{2}/{3}\r\n".format(port_item['slot_number'],
                                                                          port_item['port_number'],
                                                                          old_vpi,
                                                                          old_vci).encode('utf-8'))
                time.sleep(0.5)
                tn.write("port pvc set {0}-{1}-{2}/{3} {4} {5} {6} {7}\r\n\r\n".format(
                    port_item['slot_number'], port_item['port_number'],
                    self.__vpi,
                    self.__vci,
                    self.__profile,
                    self.__mux,
                    self.__vlan_id,
                    self.__priority).encode('utf-8'))
                time.sleep(1)
            tn.write(b"end*\r\n")
            result = tn.read_until(b'end*')
            tn.write(b"exit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            if b'example' in result:
                return {"result": "add to valn {0} give error".format(self.__vlan_id),
                        "port_indexes": self.__port_indexes, "status": 500}
            print(("{0} added to vlan {1}".format(self.__port_indexes, self.__vlan_id)))
            return dict(result="added to vlan {0}".format(self.__vlan_id), port_indexes=self.__port_indexes, status=201)
        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(str(exc_tb.tb_lineno))
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
            else:
                print(("error : add to valn {1}".format(self.__vlan_id)))
                return {"result": "add to valn {1}".format(self.__vlan_id)}

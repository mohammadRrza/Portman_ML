import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowAllVLANs(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.__vlan_name = params.get('vlan_name')
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
            res = ''
            vlan_id = None
            vlan_name = None
            uplink_vlans_id = []
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err1 = tn.read_until(b"#", 1)
            if "Login Failed." in str(err1):
                return dict(result="Telnet Username or Password is wrong! Please contact with core-access department.", status=500)
            tn.write(b"cd vlan\r\n")
            time.sleep(0.1)
            tn.write(b"show uplink vlan")
            tn.write(b"\r\n")
            time.sleep(0.1)
            tn.write(b"end\r\n")
            result = tn.read_until(b"end")
            tn.close()
            if self.request_from_ui:
                return dict(result=result.decode('utf-8'), status=200)
            result = str(result).split("\\r\\n")
            result = [val for val in result if re.search(r'\s{4,}', val)]
            return dict(result=result, status=200)

            tn.read_until(b"vlan#")
            tn.write("show service vlan interface {0}/{1}\r\n".format(self.port_conditions['slot_number'],
                                                                      self.port_conditions['port_number']).encode(
                'utf-8'))
            result = tn.read_until(b'vlan#', 0.2)
            res += str(result)
            while "vlan#" not in str(result):
                tn.write(b"\r\n")
                time.sleep(0.2)
                result = tn.read_until(b'vlan#', 0.2)
                res += str(result)
            result = str(res).split('\\r\\n')
            for val in result:
                if "cvlan" in val:
                    vlan_id = val.split()[3]
            tn.write(b'show uplink vlan\r\n')
            tn.write(b"end\r\n")
            result = tn.read_until(b"end")
            result = [re.sub(r'(\w+\s){3,}:\s\d+\s', '', val) for val in str(result).split('\\r\\n') if re.search(r'\s{4,}', val)]
            for vlan in result[1:]:
                if vlan.split()[2] == vlan_id:
                    vlan_name = vlan.split()[1]
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.close()
            return dict(vlan_id=vlan_id, vlan_name=vlan_name)
        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return str(ex) + "  // " + str(exc_tb.tb_lineno)
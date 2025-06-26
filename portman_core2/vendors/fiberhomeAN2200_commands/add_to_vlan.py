import csv
import telnetlib
import re
import time
from .command_base import BaseCommand
import sys, os

class AddToVlan(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__access_name = params.get('access_name', 'an2100')
        self.__vlan_name = params.get('vlan_name')
        self.port_conditions = params.get('port_indexes')
        self.reseller = params.get('vlan_name')
        self.device_ip = params.get('device_ip')
        self.__vpi = params.get('vpi')
        self.__vci = params.get('vci')
        self.old_vlan_name = params.get('old_vlan_name')

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

    def process_telnet_option(self, tsocket, command, option):
        from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, TTYPE, NAWS, LINEMODE, ECHO
        tsocket.sendall(IAC + WONT + LINEMODE)

    def run_command(self):
        try:
            WANE2W_par = None
            tn = telnetlib.Telnet(self.__HOST, timeout=5)
            tn.set_option_negotiation_callback(self.process_telnet_option)
            print('send login ...')
            tn.write('{0}\r\n'.format(self.__access_name).encode("utf-8"))
            err1 = tn.read_until(b"correct")
            if "incorrect" in str(err1):
                return dict(result="Access name is wrong!", status=500)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            err2 = tn.read_until(b"Password:", 1)
            if "Invalid User Name" in str(err2):
                return dict(result="User Name is wrong.", status=500)
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err3 = tn.read_until(b"OK!", 1)
            if "Invalid Password" in str(err3):
                return dict(result="Password is wrong.", status=500)
            tn.write(b"sc\r\n")
            time.sleep(1)
            WANE2W_obj = tn.read_very_eager()
            for item in str(WANE2W_obj).split('\\n\\r'):
                if 'WANE2W' in item:
                    WANE2W_par = item.split()[1]

            tn.write("ip\r\n".encode('utf-8'))
            tn.write("dfv\r\n".encode('utf-8'))
            tn.write("{0}\r\n".format(self.old_vlan_name).encode('utf-8'))
            tn.write("\r\n".encode('utf-8'))
            tn.write("0-{0}-{1}\r\n".format(self.port_conditions[0]['slot_number'],
                                            self.port_conditions[0]['port_number']).encode('utf-8'))
            time.sleep(0.5)
            tn.write("N\r\n".encode('utf-8'))
            tn.write(b"*end*\r\n")
            result = tn.read_until(b"*end*")
            if f'not a vlan {self.old_vlan_name}' in str(result):
                return dict(result=f"There isn't vlan {self.old_vlan_name}", status=500)

            tn.write("addtovlan\r\n".encode('utf-8'))
            time.sleep(0.2)
            tn.write("{0}\r\n".format(self.__vlan_name).encode('utf-8'))
            time.sleep(0.2)
            tn.write("0-{0}-1\r\n".format(WANE2W_par).encode('utf-8'))
            time.sleep(0.2)
            tn.write("0-{0}-{1}\r\n".format(self.port_conditions[0]['slot_number'],
                                            self.port_conditions[0]['port_number']).encode('utf-8'))
            time.sleep(0.2)
            tn.write("N\r\n".encode('utf-8'))
            tn.write("endn\r\n".encode('utf-8'))
            result = tn.read_until(b'endn')
            if 'System has not a vlan pte' in str(result):
                tn.write("addtovlan\r\n".encode('utf-8'))
                time.sleep(0.2)
                tn.write("isg\r\n".encode('utf-8'))
                time.sleep(0.2)
                tn.write("0-{0}-1\r\n".format(WANE2W_par).encode('utf-8'))
                time.sleep(0.2)
                tn.write("0-{0}-{1}\r\n".format(self.port_conditions[0]['slot_number'],
                                                self.port_conditions[0]['port_number']).encode('utf-8'))
                time.sleep(0.2)
                tn.write("N\r\n".encode('utf-8'))
                tn.write("end*\r\n".encode('utf-8'))
                result = tn.read_until(b'end*')
            print('===================================')
            print(result)
            print('===================================')
            tn.write(b"exit\r\n\r\n")
            if 'Continue to add port' in str(result):
                tn.write(b'core\r\n')
                tn.write(b'svc\r\n')
                tn.write(b'1\r\n')
                tn.write('0-{0}-{1}\r\n'.format(self.port_conditions[0]['slot_number'],
                                                self.port_conditions[0]['port_number']).encode('utf8'))
                time.sleep(0.5)
                output = tn.read_very_eager()
                output = str(output).split('\\n\\r')
                output = [item for item in output if re.search(r"\d+\s*/\s*\d+", item)]
                pvc = output[0].split()[0]
                wan_vpi_vci = output[0].split('/')
                wan_vpi = wan_vpi_vci[1].split()[-1]
                wan_vci = wan_vpi_vci[2].split()[0]
                tn.write(b'dvc\r\n')
                time.sleep(0.5)
                tn.write('{0}\r\n'.format(pvc).encode('utf-8'))
                time.sleep(0.5)
                tn.write(b'looptowanvc\r\n')
                tn.write('0-{0}-{1}\r\n'.format(self.port_conditions[0]['slot_number'],
                                                self.port_conditions[0]['port_number']).encode('utf8'))
                time.sleep(0.5)
                tn.write('{0}/{1}\r\n'.format(self.__vpi, self.__vci).encode('utf-8'))
                time.sleep(0.5)
                tn.write("0-{0}-1\r\n".format(WANE2W_par).encode('utf-8'))
                time.sleep(0.5)
                tn.write('{0}/{1}\r\n'.format(wan_vpi, wan_vci).encode('utf-8'))
                time.sleep(0.5)
                tn.write('{0}\r\n'.format(pvc).encode('utf-8'))
                time.sleep(0.5)
                tn.write(b"0\r\n")
                time.sleep(0.5)
                result = tn.read_very_eager()
                print('******************************')
                print(str(result))
                print('******************************')
                tn.write(b"exit\r\n")
                tn.write(b"quittelnet\r\n")
                tn.write(b"exit\r\n")
                tn.close()
                if 'field!' not in str(result):
                    result = 'port {0}-{1} added to vlan {2}'.format(self.port_conditions[0]['slot_number'],
                                                                     self.port_conditions[0]['port_number'],
                                                                     self.__vlan_name)
                    return dict(result=result, status=200)
                else:
                    result = "port {0}-{1} couldn't add to vlan {2}".format(self.port_conditions[0]['slot_number'],
                                                                            self.port_conditions[0]['port_number'],
                                                                            self.__vlan_name)
                    return dict(result=result, status=500)
            else:
                result = "port {0}-{1} couldn't add to vlan {2}".format(self.port_conditions[0]['slot_number'],
                                                                 self.port_conditions[0]['port_number'],
                                                                 self.__vlan_name)
                return dict(result=result, status=500)
        except Exception as ex:
             exc_type, exc_obj, exc_tb = sys.exc_info()
             fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
             return "Error is: {0} in line {1}".format(format(ex), str(exc_tb.tb_lineno))

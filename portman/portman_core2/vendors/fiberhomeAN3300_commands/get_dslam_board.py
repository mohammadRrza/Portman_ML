import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re

class GetDslamBoard(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__access_name = params.get('access_name','an2100')
        self.__vlan_name = params.get('vlan_name')
        self.__port_name = self.__clear_port_name(params['port_name'])
        self.__untagged_port = params.get('untagged_port')
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

    def process_telnet_option(self, tsocket, command, option):
        from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, TTYPE, NAWS, LINEMODE, ECHO
        tsocket.sendall(IAC + WONT + LINEMODE)

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST, timeout=5)
            tn.set_option_negotiation_callback(self.process_telnet_option)

            index, match_obj, text = tn.expect(
                        ['[U|u]sername: ', '[L|l]ogin:', '[L|l]oginname:', '[P|p]assword:'])

            print(index, match_obj, text)
            if index == 1:
                print('send login ...')
                tn.write('{0}\r\n'.format(self.__access_name))

            data = tn.read_until('User Name:', 5)
            print('here')
            print('==>', data)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            print('user sent ...')
            data = tn.read_until('Password:', 5)
            print('==>', data)
            tn.write(( self.__telnet_password + "\r\n").encode('utf-8'))
            print('password sent ...')

            data = tn.read_until('>', 5)
            print('got to prompt ...', data)
            tn.write("ip\r\n".encode('utf-8'))
            time.sleep(1)
            data = tn.read_until('>',5)
            tn.write("addtovlan\r\n".encode('utf-8'))
            data = tn.read_until('>',5)
            print("got to prompt 2...", data)
            time.sleep(1)
            tn.write(self.__vlan_name+"\r\n".encode('utf-8'))
            time.sleep(1)
            tn.write("0-"+self.__port_name+"\r\n".encode('utf-8'))
            time.sleep(1)
            tn.write(self.__untagged_port+"\r\n".encode('utf-8'))
            time.sleep(1)
            tn.write("n\r\n".encode('utf-8'))
            time.sleep(1)
            result = tn.read_until('>',5)
            print('===================================')
            print(result)
            print('===================================')
            tn.write("exit\r\n\r\n")
            tn.write(b'cd ..\n')
            tn.write(b'cd ..\n')
            tn.write(b'exit\r\n')
            tn.write(b'exit\r\n')
            tn.close()
            return "{0} deleted to valn {1}".format(self.__port_name, self.__vlan_name)
        except Exception as e:
            print(e)
            return "error: {0} deleted to valn {1}".format(self.__port_name, self.__vlan_name)

import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowVLAN(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__access_name = params.get('access_name', 'an2100')
        self.__port_indexes = params.get('port_indexes')
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

    def __clear_port_name(self, port_name):
        pattern = r'\d+(\s)?-(\s)?\d+'
        st = re.search(pattern, port_name, re.M | re.DOTALL)
        return st.group()

    def process_telnet_option(self, tsocket, command, option):
        from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, TTYPE, NAWS, LINEMODE, ECHO
        tsocket.sendall(IAC + WONT + LINEMODE)

    retry = 1

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST, timeout=5)
            tn.set_option_negotiation_callback(self.process_telnet_option)
            print('send login ...')
            tn.write('{0}\r\n'.format(self.__access_name).encode("utf-8"))
            err1 = tn.read_until(b"correct", 2)
            if "incorrect" in str(err1):
                tn.write(b"quittelnet\r\n")
                tn.close()
                return dict(result="Access name is wrong!", status=500)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            err2 = tn.read_until(b"Password:", 2)
            if "Invalid User Name" in str(err2):
                tn.write(b"quittelnet\r\n")
                tn.close()
                return dict(result="User Name is wrong.", status=500)
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err3 = tn.read_until(b"OK!", 2)
            if "Invalid Password" in str(err3):
                tn.write(b"quittelnet\r\n")
                tn.close()
                return dict(result="Password is wrong.", status=500)
            print('password sent ...')
            tn.write(b"ip\r\n")
            tn.write(b"sv\r\n")
            temp = tn.read_until(b'IP', 2)
            if b"NO ip uplink" in temp:
                tn.write(b"exit\r\n")
                tn.write(b"quittelnet\r\n")
                tn.close()
                return dict(result=str(temp), status=500)
            tn.read_until(b'vlan(1,2):', 2)
            tn.write(b"2\r\n")
            time.sleep(0.5)
            tn.read_until(b'(xx,xx~xx)     :', 2)
            tn.write("{0}\r\n".format(self.__vlan_name['vlan_id']).encode('utf-8'))
            time.sleep(0.5)
            tn.write(b"\r\n")
            tn.write(b"end")
            res = tn.read_until(b'end', 2)
            tn.write(b"exit\r\n")
            tn.write(b"quittelnet\r\n")
            tn.close()
            if "No specified vlan" in str(res) or "(xx,xx~xx)     :" in str(res):
                return dict(result="No specified vlan. Please try another vlan.", status=500)
            if self.request_from_ui:
                return dict(result=res.decode('utf-8'), status=200)
            result = [val for val in str(res).split("\\n\\r") if re.search(r'\s+:', val)]
            d = {}
            for b in result:
                i = b.split(' :')
                d[i[0].strip()] = i[1].replace("\\r", "").strip()
            result = d
            return dict(result=result, status=200)
        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno)))
            print(e)
            self.retry += 1
            if self.retry < 3:
                return self.run_command()

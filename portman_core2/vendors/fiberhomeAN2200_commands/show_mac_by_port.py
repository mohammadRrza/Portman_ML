import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowMacBySlotPort(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__access_name = params.get('access_name', 'an2100')
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

    def process_telnet_option(self, tsocket, command, option):
        from telnetlib import IAC, DO, DONT, WILL, WONT, SB, SE, TTYPE, NAWS, LINEMODE, ECHO
        tsocket.sendall(IAC + WONT + LINEMODE)

    retry = 1

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST, timeout=5)
            tn.set_option_negotiation_callback(self.process_telnet_option)
            print('send login ...')
            tn.write('{0}\r\n'.format(self.__access_name).encode('utf-8'))
            err1 = tn.read_until(b"correct", 2)
            if "incorrect" in str(err1):
                tn.close()
                return dict(result="Access name is wrong!", status=500)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            err2 = tn.read_until(b"Password:", 2)
            if "Invalid User Name" in str(err2):
                tn.close()
                return dict(result="User Name is wrong.", status=500)
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err3 = tn.read_until(b"OK!", 2)
            if "Invalid Password" in str(err3):
                tn.close()
                return dict(result="Password is wrong.", status=500)
            print('password sent ...')
            tn.write(b"ip\r\n")
            tn.write(b"showmac\r\n")
            time.sleep(0.5)
            tn.write(
                "0-{0}-{1}\r\n".format(self.port_conditions['slot_number'], self.port_conditions['port_number']).encode(
                    'utf-8'))
            time.sleep(1)
            tn.write(b"end\r\n")
            res = tn.read_until(b'end', 2)
            tn.write(b"exit\r\n")
            tn.write(b"quittelnet\r\n")
            tn.close()
            if "incorrect port!" in str(res):
                str_res = ["There is one of the following problems:", "This card is not configured",
                           "No card is defined on this port", "Card number is out of range.",
                           "Port number is out of range."]
                return dict(result=str_res, status=500)
            if "No Up port!" in str(res):
                return dict(result="No Up port!", status=500)
            if self.request_from_ui:
                return dict(result=res.decode('utf-8'), status=200)
            result = str(res).split("\\n\\r")
            result = [re.sub(r'\\t', '    ', val) for val in result if re.search(r'\s{2,}|--{4,}', val)]
            return dict(result=result, status=200)

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

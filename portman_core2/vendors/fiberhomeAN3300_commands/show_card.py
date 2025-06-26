import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowCard(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__vlan_name = params.get('vlan_name')
        self.__access_name = params.get('access_name', 'an3300')
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

    retry = 1

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b"end\r\n")
            err1 = tn.read_until(b"end")
            if "Login Failed." in str(err1):
                return {'result': "Telnet Username or Password is wrong! Please contact with core-access department.",
                        'status': 500}

            tn.read_until(b"User>")
            tn.write(b'admin\r\n')
            tn.read_until(b"Password:")
            tn.write('{0}\r\n'.format(self.__access_name).encode('utf-8'))
            time.sleep(0.5)
            err1 = tn.read_until(b"#", 1)
            if "Bad Password..." in str(err1):
                return {'result' :"DSLAM Password is wrong!", 'status': 500}
            tn.write(b"cd device\r\n")
            tn.write(b"show port all linelink\r\n")
            time.sleep(0.3)
            tn.read_until(b'#')
            output = tn.read_until(b'#', 0.1)
            result = ''
            result += str(output)
            while '#' not in str(output):
                tn.write(b'\r\n')
                output = tn.read_until(b'#', 0.1)
                result += str(output)

            tn.write(b"end\r\n")
            result += str(tn.read_until(b"end"))
            result = re.split(r'\\n\\r|\\r\\n|\\r|\\n', result)
            res = [item for item in result if re.search(':', item)]
            # result = str(result).replace("\\n\\n\\r", "").replace("\\r", "")
            # result = result.split("\\n")

            if "Invalid port list" in str(result):
                str_res = ["There is one of the following problems:", "This card is disable",
                           "Card number is out of range.", "Port number is out of range."]
                return dict(result=str_res, status=500)
            tn.write(b'cd ..\n')
            tn.write(b'cd ..\n')
            tn.write(b'exit\r\n')
            tn.write(b'exit\r\n')
            close_session = tn.read_until(b'Bye!', 2)
            if 'Bye' not in str(close_session):
                for i in range(4):
                    tn.write(b'exit\r\n')
                    close_session = tn.read_until(b'Bye!', 1)
                    print(str(close_session))
                    if b'Bye' in close_session:
                        break
            tn.close()
            if self.request_from_ui:
                str_join = "\r\n"
                str_join = str_join.join(res)
                return dict(result=str_join, status=200)

            return dict(result=res, status=200)

        except (EOFError, socket_error) as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno) + '//1'))
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

        except Exception as e:
            print(e)
            return str(e)

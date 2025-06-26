import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class GetConfig(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__access_name = params.get('access_name', 'an2100')
        self.__port_indexes = params.get('port_indexes')
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
            time.sleep(0.5)
            err1 = tn.read_very_eager()
            if "incorrect" in str(err1):
                tn.close()
                return dict(result="Access name is wrong!", status=500)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            time.sleep(0.5)
            err2 = tn.read_very_eager()
            if "Invalid User Name" in str(err2):
                tn.close()
                return dict(result="User Name is wrong.", status=500)
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            time.sleep(0.5)
            err3 = tn.read_very_eager()
            if "Invalid Password" in str(err3):
                tn.close()
                return dict(result="Password is wrong.", status=500)
            print('password sent ...')
            tn.write("sc\r\n".encode('utf-8'))
            time.sleep(2)
            tn.write(b'end')
            shelf_result = tn.read_until(b'end', 2)
            result = str(shelf_result).split("\\n\\r")
            result = [val for val in result if re.search(r'^\s+\d+\s+', val)]
            cards_number = []
            for item in result:
                card_number = item.split()[1]
                if 'MATCH' in item and 'COREA' not in item and 'WANE2W' not in item and 'COREC' not in item\
                        and 'COREB' not in item and 'CORED' not in item and 'WANI' not in item:
                    cards_number.append(card_number)
            command = ''
            for item in cards_number:
                command += f'0-{item}-1~32, '
            if len(command) != 0:
                tn.write(b'\r\n')
                tn.write(b'core\r\n')
                tn.write(b'svc\r\n')
                tn.write(b'1\r\n')
                tn.write('{0}\r\n'.format(command).encode('utf-8'))
            time.sleep(2)
            output = tn.read_until(b'to continue', 4)
            pvc_result = output
            while 'other key' in str(output):
                tn.write(b'\r\n')
                tn.write(b'\r\n')
                output = tn.read_until(b'to continue', 15)
                pvc_result += output
            tn.write(b'end*')
            pvc_result += tn.read_until(b'end*')
            tn.write(b'\r\n')
            tn.write(b'exit\r\n')
            tn.write(b"ip\r\n")
            tn.write(b"sv\r\n")
            temp = tn.read_until(b'IP', 2)
            tn.read_until(b'vlan(1,2):', 2)
            tn.write(b"2\r\n")
            time.sleep(0.5)
            tn.read_until(b'(xx,xx~xx)     :', 2)
            tn.write(b"\r\n")
            time.sleep(1)
            tn.write(b"\r\n")
            vlan_result = tn.read_until(b'end!', 3)
            tn.write(b"exit\r\n")
            tn.write(b"wf\r\n")
            tn.read_until(b'Programming Flash...', 15)
            tn.write(b"quittelnet\r\n")
            tn.close()
            result = vlan_result + pvc_result
            return dict(result=str(result.decode('utf-8')), status=200)

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

import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowSlotPortByMac(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__access_name = params.get('access_name', 'an2100')
        self.port_conditions = params.get('port_conditions')
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
            tn.write(b"sc\r\n")
            time.sleep(2.5)
            tn.write(b'end\r\n')
            shelf_result = tn.read_until(b'end', 2)
            shelf_result = str(shelf_result).split("\\n\\r")
            shelf_result = [val for val in shelf_result if re.search(r'^\s+\d+\s+\d+', val)]
            cards = []
            for item in shelf_result:
                cards.append(item.split()[1])
            tn.write(b"ip\r\n")
            res = ''
            for card in cards:
                print(card)
                tn.write(b"showmac\r\n")
                time.sleep(0.5)
                tn.write("0-{0}\r\n".format(card).encode('utf-8'))
                time.sleep(1)
                tn.write(b"end\r\n")
                result = tn.read_until(b'end', 2)
                if self.__mac in str(result):
                    res = result
                    break
            tn.write(b"exit\r\n")
            tn.write(b"quittelnet\r\n")
            tn.close()
            result = str(res).split('\\n\\r')
            result = [re.sub(r'\\t', '    ', val) for val in result if
                      re.search(r'\s{2,}|--{4,}', val)]
            for inx, val in enumerate(result):
                if self.__mac in val:
                    res = "".join(result[inx - 3].split("  ")[-1])
                    return dict(result=f"card: {res.split('-')[1].strip().strip()}, port: {res.split('-')[-1].strip()}", status=200)

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

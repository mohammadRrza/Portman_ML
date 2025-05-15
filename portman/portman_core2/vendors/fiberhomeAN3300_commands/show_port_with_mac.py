import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ShowPortWithMac(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.__access_name = params.get('access_name', 'an3300')
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

    retry = 1

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b"end*\r\n")
            err1 = tn.read_until(b"end*", 2)
            if "Login Failed." in str(err1):
                return "Telnet Username or Password is wrong! Please contact with core-access department."
            tn.read_until(b"User>")
            tn.write(b'admin\r\n')
            tn.read_until(b"Password:", 2)
            tn.write('{0}\r\n'.format(self.__access_name).encode('utf-8'))
            time.sleep(0.5)
            err1 = tn.read_until(b"#", 1)
            if "Bad Password..." in str(err1):
                return "DSLAM Password is wrong!"
            tn.write(b"cd device\r\n")
            tn.write(b"show slot\r\n")
            time.sleep(0.1)
            tn.write(b"\r\n")
            time.sleep(0.1)
            tn.write(b"\r\n")
            time.sleep(0.1)
            tn.write(b"\r\n")
            time.sleep(0.1)
            tn.write(b"\r\n")
            time.sleep(0.1)
            tn.write(b"end*\r\n")
            shelf_result = tn.read_until(b"end*", 2)
            shelf_result = str(shelf_result).split("\\r\\n")
            shelf_result = [val for val in shelf_result if re.search(r'^\s+\d+\s+', val)]
            cards = []
            for item in shelf_result:
                cards.append(item.split()[0])
            tn.write(b"cd fdb\r\n")
            for i in range(1, int(cards[-1])+1):
                print(i)
                tn.write("sh fdb slot {0}\r\n".format(i).encode('utf-8'))
                time.sleep(3)
                tn.write(b"\r\n")
                time.sleep(0.1)
                tn.write(b"\r\n")
                time.sleep(0.1)
                tn.write(b"\r\n")
                time.sleep(0.1)
                tn.write(b"\r\n")
                time.sleep(0.1)
                tn.write(b"end*\r\n")
                result = tn.read_until(b"end*", 1)
                if self.__mac in str(result):
                    result = str(result).split("\\r\\n")
                    result = [re.sub(r'\s+--P[a-zA-Z +\\1-9[;-]+H', '', val) for val in result if
                              re.search(r'\s{4,}[-\d\w]|-{5,}', val)]
                    for i in result:
                        if self.__mac in i:
                            card_number = i.split()[1].split(':')[0].strip()
                            port_number = i.split(':')[-2].strip()
                            return dict(result=f"card: {card_number}, port: {port_number}", status=200)

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
            return dict(result=f"MAC address '{self.__mac}' does not exits", status=500)

        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

        except Exception as e:
            print(e)
            return "error"


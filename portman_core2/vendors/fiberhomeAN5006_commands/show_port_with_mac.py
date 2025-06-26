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
        self.device_ip = params.get('device_ip')
        self.request_from_ui = params.get('request_from_ui')
        self.__mac = params.get('mac')

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
            self.__mac = self.__mac.replace(':', '')
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err1 = tn.read_until(b"#", 0.2)
            if "Login Failed." in str(err1):
                return dict(result="Telnet Username or Password is wrong! Please contact with core-access department.",
                            status=500)

            tn.write(b"cd device\r\n")
            time.sleep(0.1)
            tn.write(b"show card status\r\n")
            tn.write(b"\r\n")
            time.sleep(0.1)
            tn.write(b"end\r\n")
            shelf_result = tn.read_until(b"end")
            shelf_result = str(shelf_result).split("\\r\\n")

            shelf_result = [val for val in shelf_result if re.search(r"^\s{2,}", val)]
            cards = []
            for item in shelf_result:
                cards.append(item.split()[0].strip())
            tn.read_until(b"device#", 0.2)
            for card in cards:
                tn.write("show mac-address interface {0}/1-64\r\n".format(card).encode('utf-8'))
                time.sleep(1.5)
                tn.write(b"\r\n")
                tn.write(b"\r\n")
                print(card)
                err2 = str(tn.read_until(b"device##", 1))
                print(err2)
                if "Unknown command." in err2:
                    break
                result = err2.replace(':', '')
                if self.__mac in result:
                    result = str(result).split('\\r\\n')
                    result = [re.sub(r'\s+--P[a-zA-Z +\\1-9[;-]+J', '', val) for val in result if
                              re.search(r'\d+/\d+', val)]
                    for item in result:
                        if self.__mac in item:
                            port_number = item.split('/')[1].split()[0].strip()
                            card_number = item.split('/')[0].split()[-1]
                            return dict(result=f"card: {card_number}, port: {port_number}", status=200)
            for card in cards:
                tn.write(b"\r\n")
                tn.write(b"\r\n")
                tn.write(
                    "show linecard fdb interface {0}/1-64\r\n".format(card).encode('utf-8'))
                time.sleep(1.5)
                tn.write(b"\r\n")
                tn.write(b"\r\n")
                result = str(tn.read_until(b"device##", 0.6))
                if "Unknown command." in result:
                    break
                if self.__mac in result:
                    card_number = ''
                    result = str(result).split('\\r\\n')
                    for item in result:
                        if 'learning table' in item:
                            card_number = item.split()[-1]
                        if self.__mac in item:
                            port_number = item.split()[0]
                            return dict(result=f"card: {card_number}, port: {port_number}", status=200)

            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
            tn.write(b"exit\r\n")
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
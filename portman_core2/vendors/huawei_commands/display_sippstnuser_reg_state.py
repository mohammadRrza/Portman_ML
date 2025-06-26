import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class DisplaySippstnuserRegState(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.device_ip = params.get('device_ip')
        self.command_str = "display sippstnuser reg-state 0/{}".format(self.port_conditions['slot_number'])

    @property
    def HOST(self):
        return self.__HOST

    @HOST.setter
    def HOST(self, value):
        self.__HOST = value

    @property
    def port_name(self):
        return self.__port_name

    @port_name.setter
    def port_name(self, value):
        self.__port_name = self.__clear_port_name(value)

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

    retry = 1

    def clean_output(self, result):
        try :
            start = result.find(self.command_str)
            if start >= 0:
                result = result[start:]
        except:
            pass

        return result

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            if tn.read_until(b'>>User name:'):
                print(self.__telnet_username)
                tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
            if tn.read_until(b'>>User password:'):
                print(self.__telnet_password)
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b"q\r\n")
            tn.write(b"eenable\r\n")
            tn.write(b"enable\r\n")
            tn.write(b"config\r\n")
            tn.read_until(b"(config)#", 2)
            tn.write(b"esl user\r\n")
            time.sleep(1)
            tn.write((self.command_str + "\r\n").encode('utf-8'))
            time.sleep(0.5)
            tn.write(b'e')
            time.sleep(0.5)
            tn.write(b'e')
            time.sleep(0.5)
            tn.write(b'e')
            time.sleep(0.5)
            tn.write(b'e')
            time.sleep(0.5)
            tn.write(b"finish\r\n")
            result = tn.read_until(b'finish')
            tn.write(b"quit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            result = str(result)
            if 'Failure:' in result:
                return dict(result='The specified section is not configured with any PSTN user data', status=500)
            elif 'Parameter error' in result:
                return dict(result='This card is not defined!', status=500)

            header = ['F  /S /P    MGID    RegisterState       TelNo']
            rows = result.split('\\r\\n')
            rows = [re.sub(r"-{1,}\s*\D+\w+\D+\w+\D+\w+\D+\d*D", '', val.strip()) for val in rows if re.search(r'/\d+\s*/\d+', val)]
            return dict(src=(header + rows), result=self.clean_output(result), status=200)
        except (EOFError, socket_error) as e:
            print('============socket_error==========')
            print(e)
            print('============socket_error==========')
            self.retry += 1
            if self.retry < 4:
                return self.run_command()
        except Exception as e:
            print('============Exception==========')
            print(e)
            print('============Exception==========')
            self.retry += 1
            if self.retry < 4:
                return self.run_command()

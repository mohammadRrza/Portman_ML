import os
import sys
import telnetlib
import time
from datetime import datetime
from socket import error as socket_error
from .command_base import BaseCommand
import re

class ShowLineRate(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__port_indexes = params.get('port_conditions')
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
            tn.read_until(b'>>User name:')
            tn.write((self.__telnet_username + "\n").encode('utf-8'))
            tn.read_until(b'>>User password:')
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            result = tn.read_until(b">", 0.5)
            if 'invalid' in str(result):
                return dict(result='Telnet Username or Password is wrong! Please contact with core-access department.',
                            status=500)
            if 'Reenter times' in str(result):
                return dict(result='The device is busy right now. Please try a few moments later.',
                            status=500)
            output = str(result)
            while '>' not in str(result):
                result = tn.read_until(b">", 1)
                output += str(result)
                tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(b"enable\r\n")
            tn.read_until(b"#")
            tn.write(b"config\r\n")
            tn.read_until(b"(config)#")
            tn.write(("interface adsl 0/{0}\r\n".format(self.__port_indexes['slot_number'])).encode('utf-8'))
            result = tn.read_until(b"#")
            if "Parameter error" in str(result):
                return dict(result="Card number is wrong.", status=500)
            if "Failure:" in str(result):
                tn.write(("interface vdsl 0/{0}\r\n".format(self.__port_indexes['slot_number'])).encode('utf-8'))
                tn.read_until(b"#")
            tn.write(("display line operation {0}\r\n".format(self.__port_indexes['port_number'])).encode('utf-8'))
            time.sleep(0.5)
            tn.write(("y\r\n").encode('utf-8'))
            result = tn.read_until(b"#", 0.2)
            result += tn.read_until(b"#", 0.2)
            output = result.decode('utf-8')
            if 'idle-timeout' in output:
                result = result.decode('utf-8').replace('#', '')
            while ')#' not in str(result):
                tn.write(b"\r\n")
                result = tn.read_until(b")#", 0.1)
                output += result.decode('utf-8')
            if "Parameter error" in str(output):
                return dict(result="Port number is wrong.", status=500)
            output = output.replace('\\r\\n', '\r\n')
            output = re.sub(r"---- More.*37D", '', output)
            if self.request_from_ui:
                return dict(result=output, status=200)
            result = output.split("\r\n")
            tn.write(b"quit\r\n")
            # result = '\n'.join(eval(repr(tn.read_until(b'Upstream total output power(dBm)')).replace(r"---- More ( Press 'Q' to break ) ----\x1b[37D                                     \x1b[37D","")).split("\r\n")[:-1])
            tn.write(b"quit\r\n")
            tn.write(b"quit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            print('*******************************************')
            print(("show linerate {0}".format(result)))
            print('*******************************************')
            res = {'dslamName/cammandName': "",
                   'date': str(datetime.now()),
                   'slot/port': str(self.__port_indexes['slot_number']) + '-' + str(
                       self.__port_indexes['port_number']),
                   # 'OP_State' : res[4].split(":")[1],
                   # 'Standard' : res[5].split(":")[1],
                   # 'Latency' : res[6].split(":")[1],
                   'noisemarginDown': "",
                   'noisemarginUp': "",
                   'payloadrateDown': "",
                   'payloadrateUp': "",
                   'attenuationDown': "",
                   'attenuationUp': "",
                   # 'Tx power(D/U)' : res[10].split(":")[1].split("/")[0],
                   # 'Tx power(D/U)' : res[10].split(":")[1].split("/")[1].split(" ")[0],
                   # 'Remote vendor ID' : res[11].split(":")[1],
                   # 'Power management state' : res[12].split(":")[1],
                   # 'Remote vendor version ID' : res[13].split(":")[1],
                   # 'Loss of power(D)' : res[14].split(":")[1].split("/")[0],
                   # 'Loss of power(U)' : res[14].split(":")[1].split("/")[1].split(" ")[0],
                   # 'Loss of signal(D)' : res[15].split(":")[1].split("/")[0],
                   # 'Loss of signal(U)' : res[15].split(":")[1].split("/")[1].split(" ")[0],
                   # 'Error seconds(D)' : res[16].split(":")[1].split("/")[0],
                   # 'Error seconds(U)' : res[16].split(":")[1].split("/")[1].split(" ")[0],
                   # 'Loss by HEC collision(D)' : res[17].split(":")[1].split("/")[0],
                   # 'Loss by HEC collision(U)' : res[17].split(":")[1].split("/")[1].split(" ")[0],
                   # 'Forward correct(D)' : res[18].split(":")[1].split("/")[0],
                   # 'Forward correct(U)' : res[18].split(":")[1].split("/")[1],
                   # 'Uncorrect(D)' : res[19].split(":")[1].split("/")[0],
                   # 'Uncorrect(U)' : res[19].split(":")[1].split("/")[1],
                   'attainablerateDown': "",
                   'attainablerateUp': "",
                   'actualrateDown': "",
                   'actualrateUp': "",

                   # 'Interleaved Delay(D) ' : res[21].split(":")[1].split("/")[0],
                   # 'Interleaved Delay(U) ' : res[21].split(":")[1].split("/")[1],
                   # 'Remote loss of link' : res[22].split(":")[1],
                   }

            for inx, val in enumerate(result):
                if "Downstream channel SNR margin" in val or "Line SNR margin downstream" in val:
                    res['noisemarginDown'] = val.split(":")[1].strip()
                if "Upstream channel SNR margin" in val or "Line SNR margin upstream" in val:
                    res['noisemarginUp'] = val.split(":")[1].strip()
                if "Downstream max. attainable rate" in val or "attainable rate downstream" in val:
                    res['attainablerateDown'] = val.split(":")[1].strip()
                if "Upstream max. attainable rate" in val or "attainable rate upstream" in val:
                    res['attainablerateUp'] = val.split(":")[1].strip()
                if "Downstream actual net data rate" in val or "Actual line rate downstream" in val:
                    res['actualrateDown'] = val.split(":")[1].strip()
                if "Upstream actual net data rate" in val or "Actual line rate upstream" in val:
                    res['actualrateUp'] = val.split(":")[1].strip()
                if "Downstream channel attenuation" in val or "Line attenuation downstream" in val:
                    res['attenuationDown'] = val.split(":")[1].strip()
                if "Upstream channel attenuation" in val or "Line attenuation upstream" in val:
                    res['attenuationUp'] = val.split(":")[1].strip()

            return dict(result=res, status=200)
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
            if self.retry < 4:
                return self.run_command()

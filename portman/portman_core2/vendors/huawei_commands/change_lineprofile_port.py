import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class ChangeLineProfilePort(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.__LINE_PROFILE_OID = params.get('line_profile_oid')
        self.__port_indexes = params.get('port_conditions')
        self.__snmp_port = params.get('snmp_port', 161)
        self.__snmp_timeout = params.get('snmp_timeout', 7)
        self.__lineprofile = params.get('new_lineprofile')
        self.__set_snmp_community = params.get('set_snmp_community')
        self.device_ip = params.get('device_ip')

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

    def run_command(self):
        try:
            tn = telnetlib.Telnet(self.__HOST)
            if tn.read_until(b'>>User name:'):
                tn.write((self.__telnet_username + "\n").encode('utf-8'))
            if tn.read_until(b'>>User password:'):
                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            tn.write(b"\r\n")
            tn.write(b"\r\n")
            tn.write(b"end*\r\n")
            err = tn.read_until(b'end*', 2)
            if 'invalid' in str(err):
                return dict(result='Telnet Username or Password is wrong! Please contact with core-access department.',
                            status=500)
            if 'Reenter times' in str(err):
                return dict(result='The device is busy right now. Please try a few moments later.',
                            status=500)
            tn.write(b"\r\n")
            tn.write(b"enable\r\n")
            tn.write(b"config\r\n")
            tn.write(("interface adsl 0/{0}\r\n".format(self.__port_indexes['slot_number'])).encode('utf-8'))
            tn.write(("deactivate {0}\r\n".format(self.__port_indexes['port_number'])).encode('utf-8'))
            tn.write(("activate {0} profile-name\r\n".format(self.__port_indexes['port_number'])).encode('utf-8'))
            time.sleep(1)
            tn.write(("{0}\r\n".format(self.__lineprofile)).encode('utf-8'))
            time.sleep(1)
            tn.write(b"end*\r\n")
            result = tn.read_until(b'end*', 3)
            if 'Board type error' in str(result):
                tn.write(("interface vdsl 0/{0}\r\n".format(self.__port_indexes['slot_number'])).encode('utf-8'))
                tn.write(("deactivate {0}\r\n".format(self.__port_indexes['port_number'])).encode('utf-8'))
                tn.write(("activate {0} template-name\r\n".format(self.__port_indexes['port_number'])).encode('utf-8'))
                time.sleep(1)
                tn.write(("{0}\r\n".format(self.__lineprofile)).encode('utf-8'))
                time.sleep(1)
                tn.write(b"end*\r\n")
                result = tn.read_until(b'end*', 3)
            tn.write(b"exit\r\n")
            tn.write(b"quit\r\n")
            tn.write(b"y\r\n")
            tn.close()
            result = str(result)
            if 'Send the command to activate' in result or ('Command:' in result and 'template does not exist' not in result):
                return dict(result=f"Port's profile changed to {self.__lineprofile} successfully.", status=200)
            else:
                return dict(result='Profile change failed!', status=500)

            # target_oids_value = []
            # for index, port_item in enumerate(self.__port_indexes):
            #     target_oids_value.append(('.{0}.{1}'.format(self.__LINE_PROFILE_OID, port_item['port_index']),
            #                               rfc1902.OctetString(self.__lineprofile)))
            #     if index % 40 == 0 or index == len(self.__port_indexes):
            #         target_oids_value_tupple = tuple(target_oids_value)
            #         cmd_gen = cmdgen.CommandGenerator()
            #
            #         error_indication, error_status, error_index, var_binds = cmd_gen.setCmd(
            #             cmdgen.CommunityData(self.__set_snmp_community),
            #             cmdgen.UdpTransportTarget((self.__HOST, self.__snmp_port), timeout=self.__snmp_timeout, retries=2),
            #             *target_oids_value_tupple
            #         )
            #         target_oids_value = []
            #
            #         # Check for errors and print out results
            #         if error_indication:
            #             raise Exception(error_indication)
            #         else:
            #             if error_status:
            #                 Exception('%s at %s' % (
            #                     error_status.prettyPrint(),
            #                     error_index and var_binds[int(error_index) - 1][0] or '?'
            #                 ))
            # print('++++++++++++++++++++++')
            # # print((error_indication, error_status, error_index, var_binds))
            # print('++++++++++++++++++++++')
            # # print '------------------------------------------------------'
            # # print {"result": "ports line profile changed to {0}".format(self.__lineprofile), "port_indexes": self.__port_indexes}
            # # print '------------------------------------------------------'
            # return {"result": "ports line profile changed to {0}".format(self.__lineprofile),
            #         "port_indexes": self.__port_indexes}
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
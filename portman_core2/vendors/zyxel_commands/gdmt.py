from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
from .command_base import BaseCommand
import re
from .create_profile import CreateProfile
import telnetlib
import time
from socket import error as socket_error


class Gdmt(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.params = params
        self.__telnet_username = None
        self.__telnet_password = None
        self.__LINE_PROFILE_OID = params.get('line_profile_oid')
        self.__port_indexes = params.get('port_indexes')
        self.__snmp_port = params.get('snmp_port', 161)
        self.__snmp_timeout = params.get('snmp_timeout', 7)
        self.__lineprofile = params.get('new_lineprofile')
        self.__set_snmp_community = params.get('set_snmp_community')
        self.device_ip = params.get('device_ip')
        self.port_conditions = params.get('port_conditions')

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

    retry = 1

    def run_command(self):

        target_oids_value = []
        self.__port_indexes = [{'port_index': '{}.{}'.format(self.port_conditions['slot_number'],
                                                            self.port_conditions['port_number'])}]

        for index, port_item in enumerate(self.__port_indexes, 1):
            target_oids_value.append(('.{0}.{1}'.format(self.__LINE_PROFILE_OID, port_item['port_index']),
                                      rfc1902.OctetString(self.__lineprofile)))
            if index % 40 == 0 or index == len(self.__port_indexes):
                target_oids_value_tupple = tuple(target_oids_value)
                cmd_gen = cmdgen.CommandGenerator()

                error_indication, error_status, error_index, var_binds = cmd_gen.setCmd(
                    cmdgen.CommunityData(self.__set_snmp_community),
                    cmdgen.UdpTransportTarget((self.__HOST, self.__snmp_port), timeout=self.__snmp_timeout, retries=2),
                    *target_oids_value_tupple
                )
                target_oids_value = []

                # Check for errors and print out results
                if error_indication:
                    raise Exception(error_indication)
                else:
                    if error_status:
                        error_desc = "error: {0} send to port {1}!!!. dslam dont have line profile {2}".format(
                            error_status.prettyPrint(), port_item['port_index'], self.__lineprofile)
                        if "badValue" in error_desc:
                            return dict(result=f"DSLAM don't have line profile '{self.__lineprofile}'", status=500)

                        if 'notWritable' in error_desc:
                            try:
                                tn = telnetlib.Telnet(self.__HOST)
                                tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
                                tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
                                time.sleep(1)
                                tn.read_until(b"Password:")
                                tn.write("port adsl set {0}-{1} {2} gdmt\r\n\r\n".format(self.port_conditions['slot_number'],
                                                                                         self.port_conditions['port_number'],
                                                                                         self.__lineprofile).encode('utf-8'))
                                time.sleep(1)
                                tn.write(b"end1\r\n")
                                result = tn.read_until(b'end1')
                                if 'not supported' in str(result):
                                    tn.write("\r\nport vdsl set {0}-{1} {2} gdmt\r\n\r\n\r\n".format(
                                        self.port_conditions['slot_number'],
                                        self.port_conditions['port_number'],
                                        self.__lineprofile).encode('utf-8'))
                                    time.sleep(0.5)
                                    tn.write("port vdsl set {0}-{1} {2} gdmt\r\n\r\n\r\n".format(
                                        self.port_conditions['slot_number'],
                                        self.port_conditions['port_number'],
                                        self.__lineprofile).encode('utf-8'))

                                if "example:" in str(result):
                                    result = str(result).split("\\r\\n")
                                    result = [val for val in result if re.search(r'example|between', val)]
                                    return result
                                if "inactive" in str(result):
                                    result = str(result).split("\\r\\n")
                                    result = [val for val in result if re.search(r'inactive', val)]
                                    return result
                                if "no such profile" in str(result):
                                    return dict(result=f"Profile '{self.__lineprofile}' does not exist.", status=500)
                                tn.write(b"exit\r\n")
                                tn.write(b"y\r\n")
                                tn.close()
                                return dict(result="ports line profile changed to {0} gdmt".format(self.__lineprofile), status=200)
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
        return {"result": "ports line profile changed to {0}".format(self.__lineprofile),
                "port_indexes": self.__port_indexes}

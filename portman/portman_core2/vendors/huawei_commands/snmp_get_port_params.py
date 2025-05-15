from datetime import datetime

from easysnmp import Session, EasySNMPError
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
from .command_base import BaseCommand
import re
from .create_profile import CreateProfile
import telnetlib
import time
from socket import error as socket_error


class SNMPGetPortParam(BaseCommand):
    def __init__(self, params=None):
        self.__HOST = None
        self.params = params
        self.__telnet_username = None
        self.__telnet_password = None
        self.__ADSL_UPSTREAM_SNR = params.get('adsl_upstream_snr_oid')
        self.__ADSL_DOWNSTREAM_SNR = params.get('adsl_downstream_snr_oid')
        self.__ADSL_CURR_UPSTREAM_RATE = params.get('adsl_curr_upstream_oid')
        self.__ADSL_CURR_DOWNSTREAM_RATE = params.get('adsl_curr_downstream_oid')
        self.__port_indexes = params.get('port_indexes')
        self.__snmp_port = params.get('snmp_port', 161)
        self.__snmp_timeout = params.get('snmp_timeout', 7)
        self.__lineprofile = params.get('new_lineprofile')
        self.__get_snmp_community = params.get('get_snmp_community')
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
        if int(self.port_conditions['port_number']) < 10:
            self.port_conditions['port_number'] = '0' + self.port_conditions['port_number']
        self.__port_indexes = [{'port_index': '{}{}'.format(self.port_conditions['slot_number'],
                                                            self.port_conditions['port_number'])}]
        result = {}
        port_event_items = []
        session = Session(hostname=self.__HOST, community=self.__get_snmp_community, remote_port=self.__snmp_port,
                          timeout=5, retries=1,
                          version=2)
        try:
            print(self.__ADSL_DOWNSTREAM_SNR+".{0}".format(self.__port_indexes[0]['port_index']))
            snr_up = session.get(self.__ADSL_DOWNSTREAM_SNR+".{0}".format(self.__port_indexes[0]['port_index']))
            print('===========================================================================')
            print(snr_up)
            result['ADSL_UPSTREAM_SNR'] = snr_up.value
            snr_down = session.get(self.__ADSL_DOWNSTREAM_SNR + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_DOWNSTREAM_SNR'] = snr_down.value
            curr_down = session.get(
                self.__ADSL_CURR_DOWNSTREAM_RATE + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_CURR_DOWNSTREAM_RATE'] = curr_down.value
            curr_up = session.get(self.__ADSL_CURR_UPSTREAM_RATE + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_CURR_UPSTREAM_RATE'] = curr_up.value
            result['TIME'] = datetime.now().strftime("%H:%M:%S")

            return dict(result=result, status=200)
        except EasySNMPError as snmp_ex:
            print(snmp_ex)
        except Exception as ex:
            port_event_items.append({
                'event': '',
                'message': str(ex) + 'on {0}'.format('')
            })
            print(ex)

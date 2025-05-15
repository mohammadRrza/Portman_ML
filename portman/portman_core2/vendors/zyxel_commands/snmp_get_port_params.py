from datetime import datetime

from easysnmp import Session
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
            self.port_conditions['port_number'] = '0' + str(self.port_conditions['port_number'])
        self.__port_indexes = [{'port_index': '{}{}'.format(self.port_conditions['slot_number'],
                                                            self.port_conditions['port_number'])}]
        result = {}
        port_event_items = []
        session = Session(hostname=self.__HOST, community=self.__get_snmp_community, remote_port=self.__snmp_port,
                          timeout=5, retries=1,
                          version=2)
        try:
            snr_up = session.get(self.__ADSL_UPSTREAM_SNR + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_UPSTREAM_SNR'] = int(snr_up.value)/10
            snr_down = session.get(self.__ADSL_DOWNSTREAM_SNR + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_DOWNSTREAM_SNR'] = int(snr_down.value)/10
            curr_down = session.get(self.__ADSL_CURR_DOWNSTREAM_RATE + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_CURR_DOWNSTREAM_RATE'] = round(int(curr_down.value)/1000000, 2)
            curr_up = session.get(self.__ADSL_CURR_UPSTREAM_RATE + ".{0}".format(self.__port_indexes[0]['port_index']))
            result['ADSL_CURR_UPSTREAM_RATE'] = round(int(curr_up.value)/1000000, 2)
            result['TIME'] = datetime.now().strftime("%H:%M:%S")

            return dict(result=result, status=200)

        except Exception as ex:
            port_event_items.append({
                'event': '',
                'message': str(ex) + 'on {0}'.format('')
            })

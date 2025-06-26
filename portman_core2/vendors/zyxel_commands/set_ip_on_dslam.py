import os
import sys
import telnetlib
import time
from socket import error as socket_error
from .command_base import BaseCommand
import re


class SetIpOnDslams(BaseCommand):
    def __init__(self, params):
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.port_conditions = params.get('port_conditions')
        self.device_ip = params.get('device_ip')
        self.setPacketFilters = params.get('set_packet_filters', False)

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
        try:
            tn = telnetlib.Telnet(self.__HOST)
            tn.write((self.__telnet_username + "\n").encode('utf-8'))
            tn.read_until(b"Password:")
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))
            err1 = tn.read_until(b'Communications Corp.', 2)
            if "Password:" in str(err1):
                return dict(result="Telnet Username or Password is wrong! Please contact with core-access department.",
                            status=500)

            tn.write(b"sys client enable 1\r\n\r\n")
            tn.write(b"sys client set 1 109.125.191.0 109.125.191.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 2\r\n\r\n")
            tn.write(b"sys client set 2 5.202.129.0 5.202.129.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 3\r\n\r\n")
            tn.write(b"sys client set 3 192.168.250.0 192.168.250.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 4\r\n\r\n")
            tn.write(b"sys client set 4 192.168.251.0 192.168.251.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 5\r\n\r\n")
            tn.write(b"sys client set 5 172.28.0.0 172.28.255.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 6\r\n\r\n")
            tn.write(b"sys client set 6 5.202.112.0 5.202.122.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 7\r\n\r\n")
            tn.write(b"sys client set 7 5.202.100.0 5.202.100.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 8\r\n\r\n")
            tn.write(b"sys client set 8 185.126.16.0 185.126.19.255 telnet ftp web icmp ssh snmp https\r\n\r\n")
            tn.write(b"sys client enable 9\r\n\r\n")
            tn.write(b"sys client set 9 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 10\r\n\r\n")
            tn.write(b"sys client set 10 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 11\r\n\r\n")
            tn.write(b"sys client set 11 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 12\r\n\r\n")
            tn.write(b"sys client set 12 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 13\r\n\r\n")
            tn.write(b"sys client set 13 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 14\r\n\r\n")
            tn.write(b"sys client set 14 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 15\r\n\r\n")
            tn.write(b"sys client set 15 0.0.0.0 0.0.0.0\r\n\r\n")
            tn.write(b"sys client disable 16\r\n\r\n")
            tn.write(b"sys client set 16 0.0.0.0 0.0.0.0\r\n\r\n")

            if self.setPacketFilters:
                tn.write(b"acl pktfilter set 1-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 2-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 3-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 4-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 5-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 6-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 7-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 8-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 9-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 10-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 11-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 12-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 13-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 14-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 15-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 16-*-0/35 pppoe-only\r\n\r\n")
                tn.write(b"acl pktfilter set 17-*-0/35 pppoe-only\r\n\r\n")

            tn.write(b"config save\r\n\r\n")

            return dict(result="Ips added to DSLAMS successfully.", port_indexes=self.port_conditions, status=200)
        except (EOFError, socket_error) as e:
            print(e)
            self.retry += 1
            if self.retry < 3:
                return self.run_command()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print((str(exc_tb.tb_lineno)))
            print(e)
            self.retry += 1
            if self.retry < 3:
                return self.run_command()

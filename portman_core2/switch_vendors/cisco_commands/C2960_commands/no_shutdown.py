from netmiko import ConnectHandler
import sys, os
from .command_base import BaseCommand
import re
import paramiko
import time

class NoShutdown(BaseCommand):
    def __init__(self, params):
        self.params = params
        self.__IP = params.get('switch_ip')
        self.__SSH_username = 'it-auto' #params.get('SSH_username')
        self.__SSH_password = 'itIT' # params.get('SSH_password') #$%it@IT@@1577
        self.__SSH_port = params.get('SSH_port', 22)
        self.__SSH_timeout = params.get('SSH_timeout', 10)
        self.__FQDN = params.get('switch_fqdn')

    def run_command(self):
        try:
            interface = self.params.get('interface', '')
            description = self.params.get('description', '')
            if (description == '' and interface == ''):
                return dict(result="Description is required if interface is empty and vice versa", status=500)

            cisco_switch = {
                'device_type': 'cisco_ios',
                'ip': self.__IP,
                'username': self.__SSH_username,
                'password': self.__SSH_password
            }
            net_connect = ConnectHandler(**cisco_switch)
            net_connect.enable()

            if (interface == ''):
                configResult = self.showInterface(net_connect, description)
                success, interface, status = self.findInterfaceByDescription(configResult, description)
                if success == False:
                    net_connect.disconnect()
                    return dict(result="Could not find interface by description", status=500)

            #return interface + ":" + status
            commands = [
                "configure terminal",
                "interface {0}".format(interface),
                "no shutdown"
            ]

            output = net_connect.send_config_set(commands)
            
            net_connect.disconnect()
            return dict(result=output, status=200)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return dict(result=str(ex) + "  / Line: " + str(exc_tb.tb_lineno), status=500)

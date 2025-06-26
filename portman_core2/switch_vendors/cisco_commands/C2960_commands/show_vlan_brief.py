import datetime
import os
import sys
import paramiko
from dj_bridge import VLAN_BRIEF_PATH
from .command_base import BaseCommand


class ShowVlanBrief(BaseCommand):
    def __init__(self, params=None):

        self.__IP = params.get('switch_ip')
        self.__SSH_username = 'backup-noc'
        self.__SSH_password = 'pP78U@87aJK'
        self.__Command = 'show vlan brief'
        self.__FQDN = params.get('switch_fqdn')

    def run_command(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.__IP, username=self.__SSH_username, password=self.__SSH_password, allow_agent=False,
                           look_for_keys=False)
            stdin, stdout, stderr = client.exec_command(self.__Command)
            backup_dir = VLAN_BRIEF_PATH
            os.makedirs(backup_dir, exist_ok=True)
            f = open(backup_dir + "{0}@{1}_{2}.txt".format(
                self.__FQDN, self.__IP, str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
            for line in stdout:
                f.write(line.strip('\n'))
            f.close()
            client.close()
            return "Backup File named vlan_brief_Backups/{0}@{1}_{2}.txt has been created.".format(self.__FQDN, self.__IP, str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return str(ex) + "  // " + str(exc_tb.tb_lineno)

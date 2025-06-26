import datetime
import time
import paramiko
import sys
from .command_base import BaseCommand
from dj_bridge import MIKROTIK_ROUTER_BACKUP_PATH


class ExportVerboseTerse(BaseCommand):
    def __init__(self, params):
        self.__IP = params.get('router_ip')
        self.__SSH_username = params.get('SSH_username')
        self.__SSH_password = params.get('SSH_password')
        self.__SSH_port = params.get('SSH_port', 1001)
        self.__SSH_timeout = params.get('SSH_timeout', 10)
        self.__Command = 'export'
        self.__FQDN = params.get('router_fqdn')

    def run_command(self):
        try:
            endtime = time.time() + 30
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.__IP, username=self.__SSH_username, password=self.__SSH_password, port=self.__SSH_port, timeout=15, allow_agent=False, look_for_keys=False, banner_timeout=400)
            stdin, stdout, stderr = client.exec_command(self.__Command, get_pty=False)
            f = open(MIKROTIK_ROUTER_BACKUP_PATH + "{0}@{1}_{2}.txt".format(
                self.__IP, self.__FQDN, str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
            while not stdout.channel.eof_received:
                time.sleep(3)
                if time.time() > endtime:
                    stdout.channel.close()
                    break
            for line in iter(lambda: stdout.readline(2048), ""):
                print(stdout)
                print(line.strip('\n'))
                f.write(line.strip('\n'))
            f.close()
            client.close()
            return "Backup File named Backups/{0}_{1}.txt has been created.".format(self.__FQDN, str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')))
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            return str(ex) + "  // " + str(exc_tb.tb_lineno)

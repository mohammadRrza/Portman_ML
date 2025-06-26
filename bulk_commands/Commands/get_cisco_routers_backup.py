import datetime
import os
import sys
import paramiko
from django.db import connection
from django.http import JsonResponse
from pathlib import Path
from Commands.mail import Mail
from dj_bridge import CISCO_ROUTER_BACKUP_PATH

class GetCiscoRouterbackUp():
    def __init__(self):
        pass

    def get_device_user_pass(self, deviceInfo):
        device_username = 'backup-noc'
        device_password = 'pP78U@87aJK'

        # deviceHostGroupName = deviceInfo[4].lower()
        # if 'infrastructure' in deviceHostGroupName:
        #     device_username = 'Portman-OSS'
        #     device_password = 'GXp)@R$s8^)D^qT!'

        return [device_username, device_password]

    def run_command(self):
        mail = Mail()
        mail.from_addr = 'oss-problems@pishgaman.net'
        mail.to_addr = 'oss-problems@pishgaman.net'
        mail.msg_subject = 'Get Device Backups'
        mail.msg_body = 'Cisco Router Backup Process has been started at {0}'.format(
            str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')))
        # Mail.Send_Mail(mail)
        os.makedirs(CISCO_ROUTER_BACKUP_PATH, exist_ok=True)
        print("=============================================")
        print("Router Backup Process has been started...")
        print("=============================================")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #query = "SELECT Distinct  device_type, device_brand, device_ip, device_fqdn from zabbix_hosts where  (device_type = 'cisco_router' and device_brand = 'cisco') and device_fqdn NOT ilike  '%OLD%' and device_fqdn not ilike '%nobkp%' ORDER BY device_ip"
        query = "SELECT Distinct  zh.device_type, zh.device_brand, zh.device_ip, zh.device_fqdn, zh2.group_name from zabbix_hosts zh left join zabbix_hostgroups zh2 on zh.host_group_id  = zh2.id  where  (zh.device_type = 'cisco_router' and zh.device_brand = 'cisco') and zh.device_fqdn NOT like  '%OLD%' and zh.device_fqdn not ilike '%nobkp%' ORDER BY zh.device_ip"
        cursor = connection.cursor()
        cursor.execute(query)
        RouterObjs = cursor.fetchall()
        num = 0
        for RouterObj in RouterObjs:
            try:
                num = num+1
                print("=============================================")
                print(str(num)+'. '+RouterObj[2]+' '+RouterObj[3])
                print("=============================================")

                device_username, device_password = self.get_device_user_pass(RouterObj)
                client.connect(RouterObj[2], username=device_username,
                               password=device_password,
                               port=22, timeout=10,
                               allow_agent=False,
                               look_for_keys=False)
                stdin, stdout, stderr = client.exec_command('show run')
                f = open(CISCO_ROUTER_BACKUP_PATH + "{0}@{1}_{2}.txt".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                stdin.flush()
                for line in stdout:
                    f.write(line.strip('\n'))
                f.close()
                client.close()

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                f = open(CISCO_ROUTER_BACKUP_PATH + "Error_{0}@{1}_{2}.txt".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                f.write(str(ex) + "  // " + str(exc_tb.tb_lineno))
                f.close()
                client.close()
                print(str(ex) + " " + str(exc_tb.tb_lineno))

        return ""

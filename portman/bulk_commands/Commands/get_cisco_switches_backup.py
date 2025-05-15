import datetime
import os
import sys
import paramiko
from django.db import connection
from django.http import JsonResponse
from pathlib import Path
from Commands.mail import Mail
from dj_bridge import SWITCH_BACKUP_PATH

class GetCiscoSwitchbackUp():
    def __init__(self):
        pass

    def get_device_user_pass(self, deviceInfo):
        device_username = 'backup-noc'
        device_password = 'pP78U@87aJK'

        deviceHostGroupName = deviceInfo[4].lower()
        if 'infrastructure' in deviceHostGroupName:
            device_username = 'Portman-OSS'
            device_password = 'GXp)@R$s8^)D^qT!'

        return [device_username, device_password]


    def run_command(self):
        mail = Mail()
        mail.from_addr = 'oss-problems@pishgaman.net'
        mail.to_addr = 'oss-problems@pishgaman.net'
        mail.msg_subject = 'Get Device Backups'
        mail.msg_body = 'Cisco Switch Backup Process has been started at {0}'.format(
            str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')))
        # Mail.Send_Mail(mail)
        print("=============================================")
        print("Switch Backup Process has been started...")
        print("=============================================")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        query = "SELECT Distinct  zh.device_type, zh.device_brand, zh.device_ip, zh.device_fqdn, zh2.group_name from zabbix_hosts zh left join zabbix_hostgroups zh2 on zh.host_group_id  = zh2.id  where (zh.device_type = 'switch' or zh.device_type = 'switch_layer3') and zh.device_fqdn NOT like  '%OLD%' and zh.device_fqdn not ilike '%nobkp%' ORDER BY zh.device_ip"
        cursor = connection.cursor()
        cursor.execute(query)
        SwitchObjs = cursor.fetchall()
        num = 0
        
        os.makedirs(SWITCH_BACKUP_PATH, exist_ok=True)
        with open("/var/portman_backup/switches_with_error.txt", "w") as file:
            pass
        for SwitchObj in SwitchObjs:
            try:
                num = num+1
                print("=============================================")
                print(str(num)+'. '+SwitchObj[2]+' '+SwitchObj[3])
                print("=============================================")
                device_username, device_password = self.get_device_user_pass(SwitchObj)
                client.connect(SwitchObj[2], username=device_username,
                               password=device_password,
                               port=22, timeout=10,
                               allow_agent=False,
                               look_for_keys=False)
                stdin, stdout, stderr = client.exec_command('show run')
                f = open(SWITCH_BACKUP_PATH + "{0}@{1}_{2}.txt".format(
                    SwitchObj[3], SwitchObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                stdin.flush()
                lines = 0
                for line in stdout:
                    lines += 1
                    f.write(line)
                    # f.write(line.strip('\n'))
                f.close()
                if lines < 15:
                    with open("/var/portman_backup/switches_with_error.txt", "a") as file:
                        file.write(SwitchObj[2] + " | " + SwitchObj[3] + "\n")
                client.close()

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                f = open(SWITCH_BACKUP_PATH + "Error_{0}@{1}_{2}.txt".format(
                    SwitchObj[3], SwitchObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                f.write(str(ex) + "  // " + str(exc_tb.tb_lineno))
                f.close()
                client.close()
                print(str(ex) + " " + str(exc_tb.tb_lineno))

        return ""

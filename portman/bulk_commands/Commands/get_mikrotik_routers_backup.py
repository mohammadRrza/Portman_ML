import datetime
import os
import sys
import paramiko
from django.db import connection
from django.http import JsonResponse
from pathlib import Path
import time
from Commands.mail import Mail
from dj_bridge import MIKROTIK_ROUTER_BACKUP_PATH


class GetMikrotikbackUp():
    def __init__(self):
        pass

    def get_device_user_pass(self, deviceInfo):
        device_username = 'mik-backup'
        device_password = 'eS7*XiMmyeeU'

        deviceHostGroupName = deviceInfo[4].lower()
        if 'infrastructure' in deviceHostGroupName:
            device_username = 'Portman-OSS'
            device_password = 'GXp)@R$s8^)D^qT!'

        return [device_username, device_password]

    def run_command(self):
        ex_msg = ''
        os.makedirs(MIKROTIK_ROUTER_BACKUP_PATH, exist_ok=True)
        errors_attachment = open(MIKROTIK_ROUTER_BACKUP_PATH + "errors_attachment.txt", "w")
        endtime = time.time() + 30
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        query = "SELECT Distinct \
            zh.device_type, zh.device_brand, zh.device_ip, zh.device_fqdn, zh2.group_name from zabbix_hosts zh \
            left join zabbix_hostgroups zh2 on zh.host_group_id = zh2.id  \
            where zh.device_brand = 'mikrotik' and (zh.device_type = 'router_board' or zh.device_type = 'router_virtual') and zh.device_fqdn NOT like '%-old-%' and zh.device_fqdn NOT like '%OLD%' and zh.device_fqdn not ilike '%nobkp%' ORDER BY zh.device_ip"
        cursor = connection.cursor()
        cursor.execute(query)
        RouterObjs = cursor.fetchall()
        num = 0
        for RouterObj in RouterObjs:
            try:
                num = num + 1
                print("=============================================")
                print(str(num) + '. ' + RouterObj[2] + ' ' + RouterObj[3])
                print("=============================================")
                device_username, device_password = self.get_device_user_pass(RouterObj)
                client.connect(RouterObj[2], username=device_username,
                               password=device_password,
                               port=1001, timeout=15,
                               allow_agent=False,
                               look_for_keys=False,
                               banner_timeout=400)
                stdin, stdout, stderr = client.exec_command('export')
                #stdin, stdout, stderr = client.exec_command('export verbose terse')

                f = open(MIKROTIK_ROUTER_BACKUP_PATH + "{0}@{1}_{2}.txt".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                while not stdout.channel.eof_received:
                    time.sleep(0.5)
                    if time.time() > endtime:
                        stdout.channel.close()
                        break
                for line in iter(lambda: stdout.readline(2048), ""):
                    f.write(line.strip('\n'))
                f.close()
                client.close()

            except Exception as ex:
                print(str(ex) + " " + "35_mik")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                ex_msg = str(ex)
                if('reading SSH protocol banner' in ex_msg):
                    ex_msg = 'authentication failed.'
                f = open(MIKROTIK_ROUTER_BACKUP_PATH + "Error_{0}@{1}_{2}.txt".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                f.write(ex_msg + "  // " + str(exc_tb.tb_lineno))
                f.close()
                errors_attachment.write(ex_msg + "  // Error_{0}@{1}_{2}\n==========================================================================================\n".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))))
                client.close()
            endtime = time.time() + 30
        errors_attachment.close()
        # mail_info = Mail()
        # mail_info.from_addr = 'oss-problems@pishgaman.net'
        # mail_info.to_addr = 'm.taher@pishgaman.net, ent-network@pishgaman.net'
        # mail_info.msg_body = 'Backup routers that have encountered errors can be seen in the attached file. Please take action to fix the stated problems.'
        # mail_info.msg_subject = 'Backup Routers Error'
        # mail_info.attachment = MIKROTIK_ROUTER_BACKUP_PATH + 'errors_attachment.txt'
        # Mail.Send_Mail_With_Attachment(mail_info)
        return ""

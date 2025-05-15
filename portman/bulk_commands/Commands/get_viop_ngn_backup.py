import datetime
import os
import sys
import paramiko
from django.db import connection
from django.http import JsonResponse
from pathlib import Path
import time
from Commands.mail import Mail
from dj_bridge import VOIP_BACKUP_PATH


class GetVoipBackUp():
    def __init__(self):
        pass

    def run_command(self):
        # mail = Mail()
        # mail.from_addr = 'oss-problems@pishgaman.net'
        # mail.to_addr = 'oss-problems@pishgaman.net'
        # mail.msg_subject = 'Get Device Backups'
        # mail.msg_body = 'Mikrotik Router Backup Process has been started at {0}'.format(
        #     str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')))
        # Mail.Send_Mail(mail)
        ex_msg = ''
        if not os.path.exists(VOIP_BACKUP_PATH):
            os.makedirs(VOIP_BACKUP_PATH)
        errors_attachment = open(VOIP_BACKUP_PATH + "errors_attachment.txt", "w")
        endtime = time.time() + 10
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #         query = "SELECT Distinct  device_type, device_brand, device_ip, device_fqdn FROM zabbix_hosts where device_group in (SELECT device_type FROM zabbix_hostgroups WHERE device_name like '%Voip-NGN%' ) and device_fqdn like '%1036%' or device_fqdn like '%c2811%' or device_fqdn like '%mg.eltex%' ORDER BY device_ip"
        query = "SELECT Distinct  device_type, device_brand, device_ip, device_fqdn FROM zabbix_hosts where host_group_id in (SELECT id FROM zabbix_hostgroups WHERE group_name like '%Voip-NGN%') and (device_fqdn not like '%old%') and (device_fqdn like '%1036%' or device_fqdn like '%c2811%' or device_fqdn like '%mg.eltex%')"
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
                client.connect(RouterObj[2], username='IT-BackUP',
                               password='YdUxPv7Ja4znrE',
                               port=22, timeout=10,
                               allow_agent=False,
                               look_for_keys=False,
                               banner_timeout=200)
                stdin, stdout, stderr = client.exec_command('show run')
                #stdin, stdout, stderr = client.exec_command('export verbose terse')

                f = open(VOIP_BACKUP_PATH + "{0}@{1}_{2}.txt".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                while not stdout.channel.eof_received:
                    time.sleep(1)
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
                f = open(VOIP_BACKUP_PATH + "Error_{0}@{1}_{2}.txt".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                f.write(ex_msg + "  // " + str(exc_tb.tb_lineno))
                f.close()
                errors_attachment.write(ex_msg + "  // Error_{0}@{1}_{2}\n==========================================================================================\n".format(
                    RouterObj[3], RouterObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))))
                client.close()
            endtime = time.time() + 10
        errors_attachment.close()
        # mail_info = Mail()
        # mail_info.from_addr = 'oss-problems@pishgaman.net'
        # mail_info.to_addr = 'm.taher@pishgaman.net, ent-network@pishgaman.net'
        # mail_info.msg_body = 'Backup routers that have encountered errors can be seen in the attached file. Please take action to fix the stated problems.'
        # mail_info.msg_subject = 'Backup Routers Error'
        # mail_info.attachment = home+'/backup/voip/errors_attachment.txt'
        # Mail.Send_Mail_With_Attachment(mail_info)
        return ""

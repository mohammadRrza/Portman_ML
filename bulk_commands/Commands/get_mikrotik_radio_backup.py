import datetime
import os
import sys
import paramiko
from django.db import connection
from django.http import JsonResponse
from pathlib import Path
import time
from Commands.mail import Mail
from dj_bridge import MIKROTIK_RADIO_BACKUP_PATH

class GetMikrotikRadiobackUp():
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
        try:
            ex_msg = ''
            endtime = time.time() + 10
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            query = "SELECT Distinct  zh.device_type, zh.device_brand, zh.device_ip, zh.device_fqdn, zh2.group_name, zh.last_backup_date from zabbix_hosts zh left join zabbix_hostgroups zh2 on zh.host_group_id=zh2.id where zh.device_brand = 'mikrotik' and zh.device_type = 'wireless' and zh.device_fqdn NOT ilike  '%mimosa%' and zh.device_fqdn NOT like  '%OLD%' and zh.device_fqdn not ilike '%nobkp%' ORDER BY zh.last_backup_date asc NULLS FIRST  LIMIT 10"
            cursor = connection.cursor()
            cursor.execute(query)
            RadioObjs = cursor.fetchall()
            num = 0
            for RadioObj in RadioObjs:
                try:
                    update_query = f"UPDATE zabbix_hosts SET last_backup_date = current_timestamp WHERE device_ip = '{RadioObj[2]}'"
                    cursor.execute(update_query)
                    num = num + 1
                    print("=====================Radio========================")
                    print(str(num) + '. ' + RadioObj[2] + ' ' + RadioObj[3])
                    print("==================================================")
                    device_username, device_password = self.get_device_user_pass(RadioObj)
                    client.connect(RadioObj[2], username=device_username,
                                   password=device_password,
                                   port=1001, timeout=10,
                                   allow_agent=False,
                                   look_for_keys=False,
                                   banner_timeout=200)
                    stdin, stdout, stderr = client.exec_command('export verbose terse')

                    f = open(MIKROTIK_RADIO_BACKUP_PATH + "{0}@{1}_{2}.txt".format(
                        RadioObj[3], RadioObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
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
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    print(str(ex) + "  // " + str(exc_tb.tb_lineno))
                    ex_msg = str(ex)
                    print(ex_msg)
                    if('reading SSH protocol banner' in ex_msg):
                        ex_msg = 'authentication failed.'
                    f = open(MIKROTIK_RADIO_BACKUP_PATH + "Error_{0}@{1}_{2}.txt".format(
                        RadioObj[3], RadioObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                    f.write(ex_msg + "  // " + str(exc_tb.tb_lineno))
                    f.close()
                    client.close()

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(str(ex) + "  // " + str(exc_tb.tb_lineno))
            ex_msg = str(ex)
            print(ex_msg)
            # if('reading SSH protocol banner' in ex_msg):
            #    ex_msg = 'authentication failed.'
            # f = open(home + "/backup/mikrotik_radios/Error_{0}@{1}_{2}.txt".format(
            #      RadioObj[3], RadioObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
            # f.write(ex_msg + "  // " + str(exc_tb.tb_lineno))
            # f.close()
            # client.close()

            # mail = Mail()
            # mail.from_addr = 'oss-problems@pishgaman.net'
            # mail.to_addr = 'oss-problems@pishgaman.net'
            # mail.msg_subject = 'Get Device Backups Error'
            # mail.msg_body = 'Error: {0}----{1}'.format(str(ex) + "  // " + str(exc_tb.tb_lineno), )
            # Mail.Send_Mail(mail)
            """mail = Mail()
            mail.from_addr = 'oss-problems@pishgaman.net'
            mail.to_addr = 'oss-problems@pishgaman.net'
            mail.msg_subject = 'Get Device Backups Error'
            mail.msg_body = 'Error: {0}----{1}'.format(str(ex), str(exc_tb.tb_lineno), )
            Mail.Send_Mail(mail)"""

import datetime
import os
import sys
import paramiko
from django.db import connection
from django.http import JsonResponse
from pathlib import Path
from dj_bridge import VLAN_BRIEF_PATH

class GetVlanBrief():
    def __init__(self):
        pass

    def run_command(self):
        print("=============================================")
        print("Switch Vlan Brief Process has been started...")
        print("=============================================")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        query = "SELECT Distinct  device_type, device_brand, device_ip, device_fqdn from zabbix_hosts where  (device_type = 'switch' or device_type = 'switch_layer3') and device_fqdn NOT like  '%OLD%' ORDER BY device_ip"
        cursor = connection.cursor()
        cursor.execute(query)
        SwitchObjs = cursor.fetchall()
        num = 0
        for SwitchObj in SwitchObjs:
            try:
                num = num + 1
                print("=============================================")
                print(str(num) + '. ' + SwitchObj[2] + ' ' + SwitchObj[3])
                print("=============================================")
                client.connect(SwitchObj[2], username='backup-noc',
                               password='pP78U@87aJK',
                               port=22, timeout=10,
                               allow_agent=False,
                               look_for_keys=False)
                stdin, stdout, stderr = client.exec_command('Show vlan brief')
                if not os.path.exists(VLAN_BRIEF_PATH):
                    os.makedirs(VLAN_BRIEF_PATH)
                f = open(VLAN_BRIEF_PATH + "{0}@{1}_{2}.txt".format(
                    SwitchObj[3], SwitchObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                for line in stdout:
                    print(line)
                    f.write(line.strip('\n'))
                f.close()
                client.close()

            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                f = open(VLAN_BRIEF_PATH + "Error_{0}@{1}_{2}.txt".format(
                    SwitchObj[3], SwitchObj[2], str(datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))), "w")
                f.write(str(ex) + "  // " + str(exc_tb.tb_lineno))
                f.close()
                client.close()
                print(str(ex) + " " + str(exc_tb.tb_lineno))

        return ""

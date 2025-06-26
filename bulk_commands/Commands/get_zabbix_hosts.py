import datetime
import os
import sys

import requests
from django.db import connection
from django.http import JsonResponse
from requests import Response
from rest_framework import status

sys.path.append('/opt/portmanv3/portman_web/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

class ZabbixHosts:

    token = None
    zabbix_url = 'https://monitoring1.pishgaman.net/api_jsonrpc.php'

    def __init__(self):
        pass

    def findDeviceBrandByType(self, type):
        brand = "unknown"

        if type == 'wireless':
            return 'mikrotik'
        if type == 'engenius_wap':
            return 'Engenius'
        if type == 'olt':
            return 'huawei'

        return brand
    
    def findDeviceTypeByFQDN(self, fqdn):
        type = "unknown"

        def findByFqdn(fqdn, index=4):
            brief_name = fqdn.split('.')[index].lower()
            if brief_name in [None, '']:
                return "unknown"
            
            if brief_name in ['rou', 'hsp']:
                return "router_board";
            if brief_name in ['dsl']:
                return "dslam";
            if brief_name in ['swi']:
                return "switch";
            if brief_name in ['p2p', 'p2mp'] or 'basebox5' in fqdn or 'mimosac5c' in fqdn:
                return "wireless";
            if brief_name in ['wap']:
                return "engenius_wap";
            if brief_name in ['olt']:
                return "olt";
            if brief_name in ['ups']:
                return "ups";

        try:
            type = findByFqdn(fqdn=fqdn, index=4)
            if type in [None, '', 'unknown']:
                type = findByFqdn(fqdn=fqdn, index=5)
            if type in [None, '', 'unknown']:
                type = "unknown"
        except:
            pass       

        return type

    def get_token(self):
        if self.token == None:
            zabbix_login_data = '{"jsonrpc": "2.0","method": "user.login","params": {"user": "software","password": "ASXRQKD78kykRLT"},"id": 1,"auth": null}'
            response = requests.post(self.zabbix_url, data=zabbix_login_data, headers={"Content-Type": "application/json"})
            login = response.json()
            self.token = login['result']
        return self.token

    def update_zabbix_host_groups(self):
        zabbix_get_host_data = '{"jsonrpc": "2.0","method": "hostgroup.get","params": {"output": ["id","name"],"selectHosts": ["ip", "name", "host", "hostid"],"selectInterfaces": ["ip"]},"id": 1, "auth": "%s"}'% (self.get_token())
        host_response = requests.post(self.zabbix_url, data=zabbix_get_host_data, headers={"Content-Type": "application/json"})
        hostgroups = host_response.json()

        cursor = connection.cursor()
        cursor.execute("UPDATE zabbix_hosts SET host_group_id = null WHERE id > 0; DELETE from zabbix_hostgroups; ALTER SEQUENCE zabbix_hostgroups_id_seq RESTART WITH 1;")
        cursor.close()

        allQueries = ''
        for item in hostgroups['result']:
            allQueries += "INSERT INTO zabbix_hostgroups (group_id, group_name) values('{0}', '{1}');".format(int(item['groupid']), item['name'])

        if allQueries != '':
            cursor = connection.cursor()
            cursor.execute(allQueries)
            cursor.close()

        print("Host Group has been updated.")

    def get_zabbix_hosts(self):
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM zabbix_hostgroups")
            rows = cursor.fetchall()
            cursor.close()
            print("Group Length: ", len(rows))

            allQueries = 'DELETE from zabbix_hosts; ALTER SEQUENCE zabbix_hosts_id_seq RESTART WITH 1;'
            for row in rows:
                zabbix_get_host_data = '{"jsonrpc": "2.0","method": "host.get","params": {"groupids":["%s"],"output": ["hostid","host"],"selectInterfaces": ["ip"]},"id": 1,"auth": "%s"}'% (row[1], self.get_token())
                host_response = requests.post(self.zabbix_url, data=zabbix_get_host_data, headers={"Content-Type": "application/json"})
                hosts = host_response.json()

                print("Hosts length of Group {}-{}: ".format(row[1], row[2]), len(hosts['result']))
                for item in hosts['result']:
                    hostInfo = self.scan_host(item=item, groupInfo=row)
                    if hostInfo:
                        query = "INSERT INTO zabbix_hosts (host_id, host_group_id, device_ip, device_fqdn, last_updated, device_type, device_brand) values('{0}','{1}', '{2}', '{3}', '{4}', '{5}', '{6}');".format(hostInfo[0],hostInfo[1],
                        hostInfo[2],hostInfo[3],hostInfo[4],hostInfo[5],hostInfo[6])
                        allQueries += query
                    else:
                        print(item, "XXXXXXXXXXXXXXXxxxxxXXXXX")
                
            if allQueries != '':
                cursor = connection.cursor()
                cursor.execute(allQueries)
                cursor.close()
                
            print("All Rows Inserted.")
            return JsonResponse({'hosts': "OK"})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(ex, str(exc_tb.tb_lineno))

    def finalize(self):

        print("-----------------Updating ngn Devices")
        ngn_query = "UPDATE zabbix_hosts set device_type = 'ngn_device' where host_group_id in (SELECT id FROM zabbix_hostgroups WHERE group_name like '%Voip-NGN%') and (device_fqdn like '%1036%' or device_fqdn like '%c2811%' or device_fqdn like '%mg.eltex%')"
        cursor = connection.cursor()
        cursor.execute(ngn_query)


        print("-----------------Reading sql file")
        fd = open('Commands/insert_devices_from_zabbix.sql', 'r')
        sqlFile = fd.read()
        fd.close()
        cursor = connection.cursor()
        cursor.execute(sqlFile)
        print("The end")

    def scan_host(self, item, groupInfo):
        switch_types = ["c2960", "4948", "c9200", "c3064pq", "c9500", "c2950", "C2960X", "c4948e", "c4948", "c93180yc"]
        switch_layer3 = ["c3850", "c3750", "c4500", "c4500x", "c6816x", "c6840x", "c3172pq"]
        cisco_router = ["c2921k9", "c2811", "asr1002x", "asr1002", "asr1002hx", "asr1001x", "7200"]
        router_board = ["RB450G", "RB450", "RB750Gr3", "RB750gl", "RB750G", "RB750", "RB750R2", "CCR1009", "RB1100", "CCR1016", "CCR1036",
                        "hEX", "RB1100AHx2", "1100AHx2", "RB1100AH", "RB1100x4", "RB1100AHx4", "1100AH", "RB2011", "RB433AH", "RB433ah", "hEXRB750",
                        "750Gr3hEX", "750Gr3", "RB3011UiAS", "HexRB750", "hex", "RB600", "CCR1072", "RB750Gr2", "RB493AH", "RB2011UAS", "haplite",
                        "RB850", "1100AHx4", "RB751U", "RB1000", "RB800", "CCR1100", "RBAH433", "450G", "RB4011", "CCR1036-", "RB750R3", "RB750GL",
                        "RB100Ahx2", "RB1200", "RB260", "CCR2116", "2811", "RB2011UiAS",
                        "CCR2004", "RB1100Hx4", "RB760iGS", "750iGS", "RB951", "RB433", "433AH", "RB433AH", "RB3011", "RB951", "hex750",
                        "RB760Gr3", "rb951ui2hnd", "RB1100Hx4", "RB5009"]
        router_virtual = ["vmx86", "x86"]
        switch_board = ["CRS328", "CRS125", "CRS318", "CRS354", "CRS326"]
        wireless = ["LHG5", "LHGHP5", "LHGHP", "LHG", "LHGXL", "LHG HP5", "SXThpnd", "RB911G-5", "LHGXL5", "B921UA",
                    "RB921UAGS", "Netmetal5", "NetMetal", "Metal5", "metal5", "SXT", "SXTLite5", "SXT5", "SXT6",
                    "Mimosa", "GrooveA52", "MANTBox", "Groove52HPnr2", "MimosaB5C", "RBSXT", "Sextant", "mimosac5c", "qrt5ac",
                    "RB411AH", "Groove", "Groove5", "Groove52", "QRT", "QRT5", "DynaDish5", "daynadish5",
                    "Daynadish5", "OmniTIK5", "Netbox", "Netbox5", "RB912UAG", "RB411G", "BaseBox", "RBLHG5",
                    "BaseBox5", "Sextant5", "RB911G", "RBSXT", "SXTSQ5", "921UA", "912UAG", "RB921GS", "LHG", "nec", "alcoma",
                    "RBmetal"]
        engenius_switch = ["EWS1200"]
        engenius_wap = ["UBNT", "EWS310AP"]
        zyxel_dslam = ["Z6000", "z6000", "z1248"]
        fiberhome_dslam = ["AN2200a", "AN3300", "AN5006", "an2200a", "an3300", "an5006", "AN5006a", "an5006a"]
        huawei_dslam = ["huawei5600", "MA5616"]
        hp_switch = ["hp-v1905"]

        try:
            fqdn_type = item['host'].split('.')[5].lower()
            fqdn_type_try = item['host'].split('.')[4].lower()
            fqdn_type_try_again = item['host'].split('.')[3].lower()
            if (fqdn_type in [x.lower() for x in switch_types] or fqdn_type_try in [x.lower() for x in switch_types]):
                device_type = "switch"
                device_brand = "cisco"
            elif (fqdn_type in [x.lower() for x in hp_switch] or fqdn_type_try in [x.lower() for x in hp_switch]):
                device_type = "switch"
                device_brand = "hp"
            elif (fqdn_type in [x.lower() for x in switch_layer3] or fqdn_type_try in [x.lower() for x in switch_layer3]):
                device_type = "switch_layer3"
                device_brand = "cisco"
            elif (fqdn_type in [x.lower() for x in cisco_router] or fqdn_type_try in [x.lower() for x in cisco_router] or 
                    fqdn_type_try_again in [x.lower() for x in router_board]):
                device_type = "cisco_router"
                device_brand = "cisco"
            elif ('.rou.RB' in item['host'] or fqdn_type in [x.lower() for x in router_board] or fqdn_type_try in [x.lower() for x in router_board] or
                    fqdn_type_try_again in [x.lower() for x in router_board]):
                device_type = "router_board"
                device_brand = "mikrotik"
            elif (fqdn_type in [x.lower() for x in router_virtual] or fqdn_type_try in [x.lower() for x in router_virtual]):
                device_type = "router_virtual"
                device_brand = "mikrotik"
            elif (fqdn_type in [x.lower() for x in switch_board] or fqdn_type_try in [x.lower() for x in switch_board]):
                device_type = "switch_board"
                device_brand = "mikrotik"
            elif (fqdn_type in [x.lower() for x in wireless] or fqdn_type_try in [x.lower() for x in wireless]):
                device_type = "wireless"
                device_brand = "mikrotik"
            elif (fqdn_type in [x.lower() for x in engenius_switch] or fqdn_type_try in [x.lower() for x in engenius_switch]):
                device_type = "engenius_switch"
                device_brand = "Engenius"
            elif (fqdn_type in [x.lower() for x in engenius_wap] or fqdn_type_try in [x.lower() for x in engenius_wap]):
                device_type = "engenius_wap"
                device_brand = "Engenius"
            elif (fqdn_type in [x.lower() for x in zyxel_dslam] or fqdn_type_try in [x.lower() for x in zyxel_dslam]):
                device_type = "dslam"
                device_brand = "zyxel"
            elif '2200' in item['host'] or '3300' in item['host'] or '5006' in item['host']:
                device_type = "dslam"
                if '2200' in item['host']:
                    device_brand = "fiberhome2200"
                if '3300' in item['host']:
                    device_brand = "fiberhome3300"
                if '5006' in item['host']:
                    device_brand = "fiberhome5006"
            elif (fqdn_type in [x.lower() for x in huawei_dslam] or fqdn_type_try in [x.lower() for x in huawei_dslam]):
                device_type = "dslam"
                device_brand = "huawei"
            else:
                device_type = self.findDeviceTypeByFQDN(item['host']) #"unknown"
                device_brand = self.findDeviceBrandByType(device_type) #"unknown"
            
            return [int(item['hostid']), groupInfo[0], item['interfaces'][0]['ip'], item['host'], datetime.datetime.now(), device_type, device_brand]

        except Exception as ex:
            if 'list index out of range' in str(ex):
                return [int(item['hostid']), groupInfo[0], item['interfaces'][0]['ip'], item['host'], datetime.datetime.now(), str(ex), 'ERROR']

        return False



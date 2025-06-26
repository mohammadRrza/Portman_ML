from django.shortcuts import render

from django.db import connection
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
import requests, base64
from rest_framework import status, views, mixins, viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from classes.base_permissions import ADMIN, SUPPORT, DIRECTRESELLER, RESELLER, SUPPORT_ADMIN, BASIC
import time
from .models import Hosts


class GetFqdnFromZabbixByIpAPIView(views.APIView):

    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            ip = request.query_params.get('ip', None)
            query = "select * from zabbix_hosts where device_ip = '{}' LIMIT 1".format(ip)
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            if cursor.rowcount > 0:
                return JsonResponse({'zabbix_fqdn': rows[0]}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'response': 'No matching fqdn with this IP were found.'},
                                    status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            print(ex)
            return JsonResponse({'response': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetHostsFromZabbixAPIView(views.APIView):
    def post(self, request, format=None):
        data = request.data
        try:
            zabbix_url = 'https://zabbix.pishgaman.net/api_jsonrpc.php'
            zabbix_login_data = '{"jsonrpc": "2.0","method": "user.login","params": {"user": "software","password": "pQU5G88Xg44YbX2L"},"id": 1,"auth": null}'
            response = requests.post(zabbix_url, data=zabbix_login_data, headers={"Content-Type": "application/json"})
            login = response.json()
            token = login['result']
            zabbix_get_host_data = '{"jsonrpc": "2.0","method": "host.get","params": {"output": ["hostid","host"],"selectInterfaces": ["interfaceid","ip"]},"id": 125,"auth": "%s"}' % (
                token)
            host_response = requests.post(zabbix_url, data=zabbix_get_host_data,
                                          headers={"Content-Type": "application/json"})
            hosts = host_response.json()
            # return JsonResponse({'hosts':hosts })

            i = 1
            device = ''
            device_type = ''
            for item in hosts['result']:
                host = item['host']
                try:
                    if ('Germany' not in host):
                        device_type = host.split('.')[-2]

                    if ('dsl.' in host):
                        device = 'Dslam'
                    elif ('rou.' in host):
                        device = 'Router'
                    elif ('swi.' in host):
                        device = 'Switch'

                except Exception as ex:
                    device_type = host
                if ('dsl.' in host):
                    device = 'Dslam'
                elif ('rou.' in host):
                    device = 'Router'
                elif ('swi.' in host):
                    device = 'Switch'

                for val in item['interfaces']:
                    ip = val['ip']
                    interfaceid = val['interfaceid']

                query = "INSERT INTO zabbix_hosts values('{0}','{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(
                    int(item['hostid']),
                    device_type,
                    device_type, ip, item['host'], interfaceid, datetime.now(), device)

                cursor = connection.cursor()
                cursor.execute(query)

            return JsonResponse({'hosts': host})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return Response({'message': str(ex) + "  " + str(host)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetItemsFromZabbixAPIView(views.APIView):
    def post(self, request, format=None):
        try:
            zabbix_url = 'https://zabbix.pishgaman.net/api_jsonrpc.php'
            zabbix_login_data = '{"jsonrpc": "2.0","method": "user.login","params": {"user": "software","password": "pQU5G88Xg44YbX2L"},"id": 1,"auth": null}'
            response = requests.post(zabbix_url, data=zabbix_login_data, headers={"Content-Type": "application/json"})
            login = response.json()
            token = login['result']
            zabbix_get_items_data = '{"jsonrpc": "2.0","method": "item.get","params": {"output": "extend","hostids": "11092","search": {},"sortfield": "name"},"id": 125,"auth": "%s"}' % (
                token)
            items_response = requests.post(zabbix_url, data=zabbix_get_items_data,
                                           headers={"Content-Type": "application/json"})
            items = items_response.json()
            # for item in item['result']:

            # query = "INSERT INTO zabbix_host_items VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}, {10}, {11}, {12}, {13}, {14}, {15}, {16}, {17}, {18}, {19}, {20}, {21}, {22}, {23}, {24}, {25}, {26}, {27}, {28}, {29}, {30}, {31}, {32}, {33}, {34}, {35}, {36}, {37}, {38}, {39}, {40}, {41}, {42}, {43}, {44}, {45}, {46}, {47}, {48}, {49}, {50}, {51}, {52}, {53}, {54})";

            # cursor = connection.cursor()
            # cursor.execute(query)

            return JsonResponse({'items': items['result']})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return Response({'message': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DslamIcmpSnapshotCount(views.APIView):

    def get(self, request, format=None):
        try:
            data = request.data
            query = "select packet_loss, count(*) from dslam_dslamicmpsnapshot_y2020m12  where updated_at >= '2020-12-30 00:00:00'::timestamp  GROUP BY packet_loss";
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return JsonResponse({'pck_loss': rows})

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return Response({'message': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetInterfaceTrafficInput(views.APIView):
    def get(self, request, format=None):
        try:
            GB = 8589934592
            zabbix_url = 'https://zabbix.pishgaman.net/api_jsonrpc.php'
            zabbix_login_data = '{"jsonrpc": "2.0","method": "user.login","params": {"user": "software","password": "pQU5G88Xg44YbX2L"},"id": 1,"auth": null}'
            response = requests.post(zabbix_url, data=zabbix_login_data, headers={"Content-Type": "application/json"})
            login = response.json()
            token = login['result']
            zabbix_get_item_data = '{"jsonrpc": "2.0","method": "item.get","params": {"output": "extend","hostids": "11861","filter": {"itemid": "404525"},"sortfield": "name"},"id": 125,"auth": "%s"}' % (
                token)
            item_response = requests.post(zabbix_url, data=zabbix_get_item_data,
                                          headers={"Content-Type": "application/json"})
            item = item_response.json()
            # return JsonResponse({'item':item['result'][0]})
            return JsonResponse({'lastvalue': round(int(item['result'][0].get('lastvalue')) / GB, 4),
                                 'prevvalue': int(item['result'][0].get('prevvalue')) / GB,
                                 'lastclock': int(item['result'][0].get('lastclock')) / GB,
                                 'lastns': int(item['result'][0].get('lastns')) / GB})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return Response({'message': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ZabbixGetHistory(views.APIView):
    def post(self, request, format=None):
        try:
            data = request.data
            zabbix_item_id = data.get('zabbix_item_id')
            time_from = data.get('time_from')
            time_till = data.get('time_till')
            timestamp_from = time.mktime(datetime.strptime(time_from, "%Y/%m/%d").timetuple())
            timestamp_till = time.mktime(datetime.strptime(time_till, "%Y/%m/%d").timetuple())
            zabbix_url = 'https://zabbix.pishgaman.net/api_jsonrpc.php'
            zabbix_login_data = '{"jsonrpc": "2.0","method": "user.login","params": {"user": "software","password": "pQU5G88Xg44YbX2L"},"id": 1,"auth": null}'
            response = requests.post(zabbix_url, data=zabbix_login_data, headers={"Content-Type": "application/json"})
            login = response.json()
            token = login['result']
            zabbix_get_history_data = '{"jsonrpc": "2.0","method": "history.get","params": {"output": "extend","itemids": "%s","time_from": %s,"time_till": %s},"id": 1,"auth": "%s"}' % (
                "60288", int(timestamp_from), int(timestamp_till), token)
            history_response = requests.post(zabbix_url, data=zabbix_get_history_data,
                                             headers={"Content-Type": "application/json"})
            history = history_response.json()
            del_query = "DELETE FROM zabbix_history"
            cursor = connection.cursor()
            cursor.execute(del_query)

            for val in history['result']:
                query = "INSERT INTO zabbix_history VALUES ('{0}', '{1}', '{2}', '{3}')".format(val['itemid'],
                                                                                                val['ns'], val['value'],
                                                                                                val['clock'])
                cursor = connection.cursor()
                cursor.execute(query)

            return JsonResponse({'item': history['result']})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return Response({'message': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetFiftyFivePercent(views.APIView):
    def get(self, request, format=None):
        try:
            count_query = 'select count(*) from zabbix_history';
            cursor = connection.cursor()
            cursor.execute(count_query)
            count = cursor.fetchall()
            five_percent = (float(count[0][0]) * 5) / 100
            query = 'SELECT * from(select *, ROW_NUMBER () OVER (order by "value" DESC) from zabbix_history) x WHERE ROW_NUMBER BETWEEN {0} AND {1}'.format(
                str(five_percent - 1), str(five_percent));
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return JsonResponse(
                {'row': rows, 'five_percent': five_percent, 'Count': count[0][0], 'Losts': 8640 - int(count[0][0])})
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return Response({'message': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetFqdnFromZabbixAPIView(views.APIView):

    def get_permissions(self):
        return permissions.IsAuthenticated(),

    def get(self, request, format=None):
        try:
            fqdn = request.query_params.get('fqdn', None)
            portman_zabbix_hosts = Hosts.objects.filter(device_fqdn__icontains=str(fqdn).lower(),
                                                                     device_type='dslam').values().distinct(
                'device_fqdn')
            return Response({"zabbix_hosts": portman_zabbix_hosts},
                            status=status.HTTP_200_OK)
        except Exception as ex:
            print(ex)
            return JsonResponse({'response': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)            

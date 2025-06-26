from Commands.get_zabbix_hosts import ZabbixHosts
from Commands.get_backups import GetbackUp

if __name__ == '__main__':
    zabbix_hosts = ZabbixHosts()
    zabbix_hosts.update_zabbix_host_groups()
    zabbix_hosts.get_zabbix_hosts()
    zabbix_hosts.finalize()

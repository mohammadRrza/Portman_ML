from Commands.get_backups import GetbackUp
from Commands.get_mikrotik_routers_backup import GetMikrotikbackUp
from Commands.get_vlan_brief import GetVlanBrief
from Commands.get_cisco_switches_backup import GetCiscoSwitchbackUp
# from Commands.get_zabbix_hosts import ZabbixHosts
# from Commands.get_mikrotik_radio_backup import GetMikrotikRadiobackUp
from Commands.get_cisco_routers_backup import GetCiscoRouterbackUp
from Commands.ip_service_set import SetIPService
from Commands.get_viop_ngn_backup import GetVoipBackUp
from Commands.get_dslam_port_params import GetDslamPortParams
from services.packet_loss_service import PacketLoss
from services.ticket_service import Ticket
from services.delete_portman_log import delete_log
from services.check_ping_service import check_routers_ping, check_switch_ping
from services.routers_backup_error import create_ticket


def get_packet_loss():
    obj_packet_loss = PacketLoss()
    obj_packet_loss.check_packet()


# def get_zabbix_hosts():
#     zabbix_hosts = ZabbixHosts()
#     zabbix_hosts.get_zabbix_hosts()


def get_cisco_switches_backup():
    cisco_switches_backup = GetCiscoSwitchbackUp()
    cisco_switches_backup.run_command()


def get_mikrotik_routers_backup():
    mikrotik_routers_backup = GetMikrotikbackUp()
    mikrotik_routers_backup.run_command()


def get_vlan_brief():
    get_vlan_brief = GetVlanBrief()
    get_vlan_brief.run_command()


def get_cisco_routers_backup():
    cisco_routers_backup = GetCiscoRouterbackUp()
    cisco_routers_backup.run_command()


# def get_radio_backup():
#     radio_backup = GetMikrotikRadiobackUp()
#     radio_backup.run_command()


def set_ip_service():
    set_ip_service_obj = SetIPService()
    set_ip_service_obj.run_command()


def get_viop_ngn_backup():
    voip_ngn_backup = GetVoipBackUp()
    voip_ngn_backup.run_command()


def check_ping():
    check_routers_ping()
    check_switch_ping()


def ticket_routers_backup_error():
    create_ticket()


if __name__ == '__main__':
    '''back_up = GetbackUp()
    print('Backup process is started.')
    back_up.run_command()
    ip_service_set = SetIPService()
    ip_service_set.run_command()'''
    
    get_mikrotik_routers_backup()
    get_cisco_routers_backup()
    get_cisco_switches_backup()
    get_vlan_brief()
    delete_log()
    get_packet_loss()
    get_viop_ngn_backup()
    #check_ping()
    ###ticket_routers_backup_error()

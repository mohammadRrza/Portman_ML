import time
import csv
from datetime import datetime
from collections import defaultdict
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
from vendors.base import BaseDSLAM
import telnetlib
from easysnmp import Session
import re
from .command_factory import CommandFactory
from .zyxel_commands.selt import Selt
from .zyxel_commands.show_mac_slot_port import ShowMacSlotPort
from .zyxel_commands.show_mac import ShowMac
from .zyxel_commands.lcman_show import LcmanShow
from .zyxel_commands.profile_adsl_show import ProfileADSLShow
from .zyxel_commands.profile_vdsl_show import ProfileVDSLShow
from .zyxel_commands.create_profile import CreateProfile
from .zyxel_commands.delete_profile import DeleteProfile
from .zyxel_commands.lcman_disable_slot import LcmanDisableSlot
from .zyxel_commands.lcman_reset_slot import LcmanResetSlot
from .zyxel_commands.lcman_enable_slot import LcmanEnableSlot
from .zyxel_commands.lcman_show_slot import LcmanShowSlot
from .zyxel_commands.port_disable import PortDisable
from .zyxel_commands.port_enable import PortEnable
from .zyxel_commands.port_pvc_set import PortPvcSet
from .zyxel_commands.port_pvc_delete import PortPvcDelete
from .zyxel_commands.add_to_vlan import AddToVlan
from .zyxel_commands.create_vlan import CreateVlan
from .zyxel_commands.vlan_show import VlanShow
from .zyxel_commands.change_admin_status import ChangeAdminStatus
from .zyxel_commands.reset_admin_status import ResetAdminStatus
from .zyxel_commands.change_lineprofile_port import ChangeLineProfilePort
from .zyxel_commands.switch_mac_flush_all import SwitchMacFlushAll
from .zyxel_commands.get_dslam_board import GetDSLAMBoard
from .zyxel_commands.sys_snmp_setcommunity import SysSnmpSetCommunity
from .zyxel_commands.sys_snmp_getcommunity import SysSnmpGetCommunity
from .zyxel_commands.show_lineinfo import ShowLineInfo
from .zyxel_commands.show_linerate import ShowLineRate
from .zyxel_commands.show_linestat_port import ShowLineStatPort
from .zyxel_commands.show_linestat_slot import ShowLineStatSlot
from .zyxel_commands.show_performance import ShowPerformance
from .zyxel_commands.acl_maccount_set import AclMaccountSet
from .zyxel_commands.enable_annexm import EnableAnnexm
from .zyxel_commands.disable_annexm import DisableAnnexm
from .zyxel_commands.port_pvc_show import PortPvcShow
from .zyxel_commands.port_info import PortInfo
from .zyxel_commands.removeFromVlan import RemoveFromVlan
from .zyxel_commands.get_backup import GetBackUp
from .zyxel_commands.set_time import SetTime
from .zyxel_commands.show_slot_port_with_mac import ShowSlotPortWithMac
from .zyxel_commands.port_pvc_show import PortPvcShow
from .zyxel_commands.version import ShowVersion
from .zyxel_commands.show_card_info import ShowCardInfo
from .zyxel_commands.port_reset import PortReset
from .zyxel_commands.profile_vdsl_set import ProfileVDSLSet
from .zyxel_commands.show_snmp import ShowSNMP
from .zyxel_commands.show_ip import ShowIP
from .zyxel_commands.ip_arp_show import IPARPShow
from .zyxel_commands.sys_info_show import SysInfoShow
from .zyxel_commands.sys_client_show import SysClientShow
from .zyxel_commands.acl_maccount_show import ACLMacCountShow
from .zyxel_commands.acl_pktfilter_show import ACLPktfilterShow
from .zyxel_commands.acl_pppoeagent_show import ACLPPPoEAgentShow
from .zyxel_commands.switch_port_show import SwitchPortShow
from .zyxel_commands.save_config import SaveConfig
from .zyxel_commands.set_ip_on_dslam import SetIpOnDslams
from .zyxel_commands.snmp_get_port_params import SNMPGetPortParam
from .zyxel_commands.get_traffic import GetTraffic
from .zyxel_commands.show_shelf_by_card import ShowShelfCard
from .zyxel_commands.cards_status import CardsStatus
from .zyxel_commands.gdmt import Gdmt

from datetime import timedelta


class Zyxel(BaseDSLAM):
    command_factory = CommandFactory()
    command_factory.register_type('showSelt', Selt)
    command_factory.register_type('show mac by slot port', ShowMacSlotPort)
    command_factory.register_type('show mac', ShowMac)
    command_factory.register_type('show lineinfo', ShowLineInfo)
    command_factory.register_type('show linerate', ShowLineRate)
    command_factory.register_type('show linestat port', ShowLineStatPort)
    command_factory.register_type('Show Card', ShowLineStatSlot)
    command_factory.register_type('show performance', ShowPerformance)
    command_factory.register_type('profile adsl show', ProfileADSLShow)
    command_factory.register_type('profile vdsl show', ProfileVDSLShow)
    command_factory.register_type('profile vdsl set', ProfileVDSLSet)
    command_factory.register_type('Show Shelf', LcmanShow)
    command_factory.register_type('profile adsl delete', DeleteProfile)
    command_factory.register_type('lcman disable slot', LcmanDisableSlot)
    command_factory.register_type('lcman reset slot', LcmanResetSlot)
    command_factory.register_type('lcman enable slot', LcmanEnableSlot)
    command_factory.register_type('lcman show slot', LcmanShowSlot)
    command_factory.register_type('port disable', PortDisable)
    command_factory.register_type('port enable', PortEnable)
    command_factory.register_type('port reset', PortReset)
    command_factory.register_type('port pvc set', PortPvcSet)
    command_factory.register_type('port pvc delete', PortPvcDelete)
    command_factory.register_type('add to vlan', AddToVlan)
    command_factory.register_type('create vlan', CreateVlan)
    command_factory.register_type('Show All VLANs', VlanShow)
    command_factory.register_type('setPortProfiles', ChangeLineProfilePort)
    command_factory.register_type('change admin status', ChangeAdminStatus)
    command_factory.register_type('reset admin status', ResetAdminStatus)
    command_factory.register_type('switch mac flush all', SwitchMacFlushAll)
    command_factory.register_type('get dslam board', GetDSLAMBoard)
    command_factory.register_type('show snmp community', ShowSNMP)
    command_factory.register_type('sys snmp setcommunity', SysSnmpSetCommunity)
    command_factory.register_type('sys snmp getcommunity', SysSnmpGetCommunity)
    command_factory.register_type('acl maccount set', AclMaccountSet)
    command_factory.register_type('enable annexm', EnableAnnexm)
    command_factory.register_type('disable annexm', DisableAnnexm)
    command_factory.register_type('show pvc by port', PortPvcShow)
    command_factory.register_type('port Info', PortInfo)
    command_factory.register_type('port pvc show', PortPvcShow)
    command_factory.register_type('delete from vlan', RemoveFromVlan)
    command_factory.register_type('get config', GetBackUp)
    command_factory.register_type('set time', SetTime)
    command_factory.register_type('show port with mac', ShowSlotPortWithMac)
    command_factory.register_type('Version', ShowVersion)
    command_factory.register_type('show card info', ShowCardInfo)
    command_factory.register_type('IP Show', ShowIP)
    command_factory.register_type('ip arp show', IPARPShow)
    command_factory.register_type('sys info show', SysInfoShow)
    command_factory.register_type('sys client show', SysClientShow)
    command_factory.register_type('acl maccount show', ACLMacCountShow)
    command_factory.register_type('acl pktfilter show', ACLPktfilterShow)
    command_factory.register_type('acl pppoeagent show', ACLPPPoEAgentShow)
    command_factory.register_type('switch port show', SwitchPortShow)
    command_factory.register_type('save config', SaveConfig)
    command_factory.register_type('set ip on dslams', SetIpOnDslams)
    command_factory.register_type('snmp get port params', SNMPGetPortParam)
    command_factory.register_type('get traffic', GetTraffic)
    command_factory.register_type('show shelf by card', ShowShelfCard)
    command_factory.register_type('cards status', CardsStatus)
    command_factory.register_type('gdmt', Gdmt)

    EVENT = {'dslam_connection_error': 'DSLAM Connection Error', 'no_such_object': 'No Such Objects'}
    EVENT_INVERS = dict(list(zip(list(EVENT.values()), list(EVENT.keys()))))

    PORT_DETAILS_OID_TABLE = {
        "1.3.6.1.2.1.2.2.1.7": "PORT_ADMIN_STATUS",
        "1.3.6.1.2.1.2.2.1.8": "PORT_OPER_STATUS",
        "1.3.6.1.2.1.10.94.1.1.1.1.4": "LINE_PROFILE",
        "1.3.6.1.2.1.10.94.1.1.2.1.4": "ADSL_UPSTREAM_SNR",
        "1.3.6.1.2.1.10.94.1.1.2.1.5": "ADSL_UPSTREAM_ATTEN",
        "1.3.6.1.2.1.10.94.1.1.2.1.8": "ADSL_UPSTREAM_ATT_RATE",
        "1.3.6.1.2.1.10.94.1.1.5.1.2": "ADSL_CURR_UPSTREAM_RATE",
        "1.3.6.1.2.1.10.94.1.1.3.1.4": "ADSL_DOWNSTREAM_SNR",
        "1.3.6.1.2.1.10.94.1.1.3.1.5": "ADSL_DOWNSTREAM_ATTEN",
        "1.3.6.1.2.1.10.94.1.1.3.1.8": "ADSL_DOWNSTREAM_ATT_RATE",
        "1.3.6.1.2.1.10.94.1.1.4.1.2": "ADSL_CURR_DOWNSTREAM_RATE",
        "1.3.6.1.2.1.31.1.1.1.10": "OUTGOING_TRAFFIC",
        "1.3.6.1.2.1.31.1.1.1.6": "INCOMING_TRAFFIC"
    }


    PORT_DETAILS_OID_TABLE_INVERSE = {v: k for k, v in list(PORT_DETAILS_OID_TABLE.items())}

    PORT_ADMIN_STATUS = {1: "UNLOCK", 2: "LOCK", 3: "TESTING"}
    PORT_ADMIN_STATUS_INVERSE = {v: k for k, v in list(PORT_ADMIN_STATUS.items())}

    PORT_OPER_STATUS = {1: "SYNC", 2: "NO-SYNC", 3: "TESTING",
                        4: "UNKNOWN", 5: "DORMANT", 6: "NOT-PRESENT",
                        7: "LOWER-LAYER-DOWN", 65536: "NO-SYNC-GENERAL"}
    PORT_OPER_STATUS_INVERSE = {v: k for k, v in list(PORT_OPER_STATUS.items())}

    PORT_INDEX_TO_PORT_NAME_OID = '1.3.6.1.2.1.2.2.1.2'
    PORT_UPTIME_OID = '1.3.6.1.2.1.2.2.1.9'
    HOSTName_OID = '1.3.6.1.2.1.1.5.0'
    VPI_OID = '1.3.6.1.4.1.890.1.5.13.5.1.4.3.1.1'
    VCI_OID = '1.3.6.1.4.1.890.1.5.13.5.1.4.3.1.2'
    SYS_UP_TIME = '1.3.6.1.2.1.1.3.0'

    @classmethod
    def translate_event_by_text(cls, event):
        if event in cls.EVENT_INVERS:
            return cls.EVENT_INVERS[event]
        return None

    @classmethod
    def translate_admin_status_by_text(cls, admin_status):
        admin_status = admin_status.upper()
        if admin_status in cls.PORT_ADMIN_STATUS_INVERSE:
            return cls.PORT_ADMIN_STATUS_INVERSE[admin_status]
        return None

    @classmethod
    def translate_admin_status_by_value(cls, admin_status_val):
        if not admin_status_val.isdigit():
            return admin_status_val

        admin_status_val = int(admin_status_val)
        if admin_status_val in cls.PORT_ADMIN_STATUS:
            return cls.PORT_ADMIN_STATUS[admin_status_val]
        return admin_status_val

    @classmethod
    def translate_oper_status_by_value(cls, oper_status_val):
        if not oper_status_val.isdigit():
            return oper_status_val

        oper_status_val = int(oper_status_val)
        if oper_status_val in cls.PORT_OPER_STATUS:
            return cls.PORT_OPER_STATUS[oper_status_val]
        return oper_status_val

    @classmethod
    def get_dslam_info(cls, dslam_data):
        dslam_ip = dslam_data['ip']
        snmp_community = dslam_data['get_snmp_community']
        snmp_port = int(dslam_data.get('snmp_port', 161))
        snmp_timeout = int(dslam_data.get('snmp_timeout', 5))
        try:
            session = Session(hostname=dslam_ip, community=snmp_community, remote_port=snmp_port, timeout=snmp_timeout,
                              retries=1, version=2)

            try:
                dslam_hostname = session.get(cls.HOSTName_OID).value
            except Exception as ex:
                print(ex)
                dslam_hostname = 'error'

            try:
                sys_up_time = session.get(cls.SYS_UP_TIME)
                seconds = int(sys_up_time.value) / 100
                dslam_uptime = "{:0>8}".format(timedelta(seconds=seconds))
            except Exception as ex:
                print(ex)
                uptime = 'error'
        except Exception as ex:
            print(ex)
            return None, None
        return (dslam_uptime, dslam_hostname)

    @classmethod
    def get_port_index_mapping(cls, dslam_data):
        """
        Get Ports Status and dslam information
        """
        info = {}
        start = time.time()
        port_index_mapping = []
        dslam_ip = dslam_data['ip']
        snmp_community = dslam_data['get_snmp_community']
        snmp_port = int(dslam_data.get('snmp_port', 161))
        snmp_timeout = int(dslam_data.get('snmp_timeout', 5))
        try:
            session = Session(hostname=dslam_ip, community=snmp_community, remote_port=snmp_port, timeout=snmp_timeout,
                              retries=1, version=2)
            var_binds = session.walk(cls.PORT_INDEX_TO_PORT_NAME_OID)
            for item in var_binds:
                if 'adsl' in item.value:
                    slot_number = re.search(r'\d{1,4}', item.value).group()
                    port_number = re.search(r'\d{1,4}$', item.value).group()
                    if 'ifDescr' in item.oid:
                        port_index_mapping.append((slot_number, port_number, item.oid_index, item.value))
                    else:
                        port_index_mapping.append((slot_number, port_number, item.oid.split('.')[-1], item.value))

            du = time.time() - start
        except Exception as e:
            print(e)
            info['dslam_events'] = (dslam_data['id'], cls.translate_event_by_text('DSLAM Connection Error'), e)
        finally:
            info['port_index_mapping'] = port_index_mapping
            return info

    @classmethod
    def get_current_port_status(cls, dslam_data, slot_number, port_number, port_index):
        port_results = {}
        port_current_status = {}
        snmp_community = dslam_data['get_snmp_community']
        dslam_ip = dslam_data['ip']
        snmp_port = int(dslam_data.get('snmp_port', 161))
        snmp_timeout = int(dslam_data.get('snmp_timeout', 5))
        port_event_items = []
        session = Session(hostname=dslam_ip, community=snmp_community, remote_port=snmp_port, timeout=5, retries=1,
                          version=2)
        for oid, item_name in list(cls.PORT_DETAILS_OID_TABLE.items()):
            try:
                var_bind = session.get(oid + ".{0}".format(port_index))
            except Exception as ex:
                port_event_items.append({
                    'event': cls.translate_event_by_text('DSLAM Connection Error'),
                    'message': str(ex) + 'on {0}'.format(item_name)
                })
                continue

            if 'No Such' in var_bind.value or 'NOSUCH' in var_bind.value:  # Ignore this item since we have no data
                port_event_items.append({
                    'event': cls.translate_event_by_text('No Such Objects'),
                    'message': 'error on ' + item_name
                })
                continue

            if item_name == 'PORT_ADMIN_STATUS':
                value = cls.translate_admin_status_by_value(var_bind.value)
            elif item_name == 'PORT_OPER_STATUS':
                value = cls.translate_oper_status_by_value(var_bind.value)
            elif item_name in ('ADSL_UPSTREAM_ATT_RATE', 'ADSL_DOWNSTREAM_ATT_RATE', 'ADSL_CURR_UPSTREAM_RATE',
                               'ADSL_CURR_DOWNSTREAM_RATE'):
                value = int(var_bind.value) / 8192
            else:
                value = var_bind.value

            port_current_status[item_name] = value

        # get uptime port
        uptime = 0
        if int(port_number) < 10:
            port_number = '0' + str(port_number)
        try:
            port_last_change_var = session.get('{0}.{1}{2}'.format(cls.PORT_UPTIME_OID, slot_number, port_number))
            sys_up_time_var = session.get(cls.SYS_UP_TIME)
            port_up_time_value = int(sys_up_time_var.value) - int(port_last_change_var.value)
        except Exception as ex:
            port_up_time_value = 100

        if port_up_time_value:
            port_up_time_tikcs = int(port_up_time_value)
            seconds = port_up_time_tikcs / 100
            print('=======================================')
            print(timedelta(seconds=seconds))
            port_up_time = "{:0>8}".format(str(timedelta(seconds=seconds)))
            uptime = port_up_time

        port_current_status['ADSL_UPTIME'] = uptime

        if 'ADSL_UPSTREAM_ATTEN' in port_current_status:
            port_current_status['ADSL_UPSTREAM_ATTEN_FLAG'] = cls.get_atten_flag(
                float(port_current_status['ADSL_UPSTREAM_ATTEN']) / 10)

        if 'ADSL_DOWNSTREAM_ATTEN' in port_current_status:
            port_current_status['ADSL_DOWNSTREAM_ATTEN_FLAG'] = cls.get_atten_flag(
                float(port_current_status['ADSL_DOWNSTREAM_ATTEN']) / 10)

        if 'ADSL_UPSTREAM_SNR' in port_current_status:
            port_current_status['ADSL_UPSTREAM_SNR_FLAG'] = cls.get_snr_flag(
                float(port_current_status['ADSL_UPSTREAM_SNR']) / 10)

        if 'ADSL_DOWNSTREAM_SNR' in port_current_status:
            port_current_status['ADSL_DOWNSTREAM_SNR_FLAG'] = cls.get_snr_flag(
                float(port_current_status['ADSL_DOWNSTREAM_SNR']) / 10)

        port_results['port_current_status'] = port_current_status
        port_results['port_events'] = {'dslam_id': dslam_data['id'], 'slot_number': slot_number,
                                       'port_number': port_number, 'port_event_items': port_event_items}

        port_results['fetched_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return port_results

    @classmethod
    def get_atten_flag(cls, atten_value):
        if atten_value <= 20:
            return 'outstanding'
        elif atten_value > 20 and atten_value <= 30:
            return 'excellent'
        elif atten_value > 30 and atten_value <= 40:
            return 'very_good'
        elif atten_value > 40 and atten_value <= 50:
            return 'good'
        elif atten_value > 50 and atten_value <= 60:
            return 'poor'
        else:
            return 'bad'

    @classmethod
    def get_snr_flag(cls, snr_value):
        if snr_value <= 6:
            return 'bad'
        elif snr_value > 6 and snr_value <= 10:
            return 'fair'
        elif snr_value > 10 and snr_value <= 20:
            return 'good'
        elif snr_value > 20 and snr_value <= 29:
            return 'excellent'
        else:
            return 'outstanding'

    @classmethod
    def get_current_port_status_bulk(cls, dslam_info, dslam_port_map):
        start = time.time()
        snmp_community = dslam_info['get_snmp_community']
        dslam_ip = dslam_info['ip']
        snmp_port = int(dslam_info.get('snmp_port', 161))
        snmp_timeout = int(dslam_info.get('snmp_timeout', 5))
        # dslam_port_map = cls._get_all_port_mappings(dslam)
        port_mapping_len = len(dslam_port_map)
        ports_status = {}
        cmd_gen = cmdgen.CommandGenerator()
        oid_list = [
            # cls.PORT_DETAILS_OID_TABLE_INVERSE['PORT_ADMIN_STATUS'],
            # cls.PORT_DETAILS_OID_TABLE_INVERSE['PORT_OPER_STATUS'],
            # cls.PORT_DETAILS_OID_TABLE_INVERSE['LINE_PROFILE'],
            # cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_CURR_DOWNSTREAM_RATE'],
            # cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_CURR_UPSTREAM_RATE'],
            cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_DOWNSTREAM_SNR'],
            cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_UPSTREAM_SNR']
        ]

        # session = Session(hostname=dslam_ip, community=snmp_community, remote_port=snmp_port,timeout=snmp_timeout, retries=3,version=2)
        # var_bind_table = session.get_bulk(*oid_list,0,port_mapping_len)

        error_indication, error_status, \
        error_index, var_bind_table = cmd_gen.bulkCmd(
            cmdgen.CommunityData(snmp_community),
            cmdgen.UdpTransportTarget((dslam_ip, snmp_port),
                                      timeout=snmp_timeout, retries=2),
            0, port_mapping_len, *oid_list
        )

        if error_indication:
            raise Exception(error_indication)
        else:
            if error_status:
                raise Exception('%s at %s' % (
                    error_status.prettyPrint(),
                    error_index and var_bind_table[-1][int(error_index) - 1] or '?'
                ))

            else:
                for row in var_bind_table:
                    for oid, val in row:
                        # oid, port_index = cls._resolve_oid(oid.prettyPrint())
                        oid, port_index = cls._resolve_oid(str(oid))
                        port_name = dslam_port_map[port_index]
                        item_name = cls.PORT_DETAILS_OID_TABLE[oid]
                        if port_name not in ports_status:
                            ports_status[port_name] = {}
                        ports_status[port_name][item_name] = val.prettyPrint()
                        ports_status[port_name][
                            'fetched_at'
                        ] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        du = time.time() - start
        print(('======================= Get Port Status Bulk Donw in %s' % du))
        return ports_status

    @classmethod
    def _resolve_oid(cls, oid):
        """
        Given an OID, return the parent OID part and Port-Index
        """
        oid = oid.split('.')
        port_index = oid[-1]
        oid = '.'.join(oid[:-1])
        return oid, port_index

    @classmethod
    def get_port_vpi_vci(cls, dslam_info):
        snmp_community = dslam_info['set_snmp_community']
        dslam_ip = dslam_info['ip']
        snmp_port = int(dslam_info.get('snmp_port', 161))
        snmp_timeout = int(dslam_info.get('snmp_timeout', 5))
        session = Session(hostname=dslam_ip, community=snmp_community, remote_port=snmp_port, timeout=5, retries=1,
                          version=2)
        info = {}
        port_vpi_vci = defaultdict(dict)
        try:
            start = time.time()
            session = Session(hostname=dslam_ip, community=snmp_community, remote_port=snmp_port, timeout=snmp_timeout,
                              retries=1, version=2)
            var_binds = session.walk(cls.VPI_OID)
            for item in var_binds:
                port_index = item.oid.split('.')[-3]
                port_vpi_vci[port_index]['vpi'] = item.value

            var_binds = session.walk(cls.VCI_OID)
            for item in var_binds:
                port_index = item.oid.split('.')[-3]
                port_vpi_vci[port_index]['vci'] = item.value
                port_vpi_vci[port_index]['port_index'] = port_index

            du = time.time() - start
        except Exception as e:
            print(e)
            info['dslam_events'] = (dslam_data['id'], cls.translate_event_by_text('DSLAM Connection Error'), e)
        finally:
            info['port_vpi_vci'] = list(port_vpi_vci.values())
            return info

    @classmethod
    def change_port_admin_status(cls, dslam_info, port_index, admin_status):
        # port_index = cls.resolve_port_name(dslam, port_name)
        admin_status = cls.translate_admin_status_by_text(admin_status)
        snmp_community = dslam_info['set_snmp_community']
        dslam_ip = dslam_info['ip']
        snmp_port = int(dslam_info.get('snmp_port', 161))
        snmp_timeout = int(dslam_info.get('snmp_timeout', 5))

        target_oid = '.{0}.{1}'.format(cls.PORT_DETAILS_OID_TABLE_INVERSE['PORT_ADMIN_STATUS'], port_index)

        if admin_status is None:
            raise Exception('Invalid Admin Status Value')

        cmd_gen = cmdgen.CommandGenerator()

        error_indication, error_status, error_index, var_binds = cmd_gen.setCmd(
            cmdgen.CommunityData(snmp_community),
            cmdgen.UdpTransportTarget((dslam_ip, snmp_port),
                                      timeout=snmp_timeout, retries=2),

            (target_oid, rfc1902.Integer(admin_status))
        )

        # Check for errors and print out results
        if error_indication:
            raise Exception(error_indication)
        else:
            if error_status:
                Exception('%s at %s' % (
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or '?'
                ))

        return True

    @classmethod
    def reset_adminstatus(cls, dslam_info, port_index):

        snmp_community = dslam_info['set_snmp_community']
        dslam_ip = dslam_info['ip']
        snmp_port = int(dslam_info.get('snmp_port', 161))
        snmp_timeout = int(dslam_info.get('snmp_timeout', 5))
        target_oid = '.{0}.{1}'.format(cls.PORT_DETAILS_OID_TABLE_INVERSE['PORT_ADMIN_STATUS'], port_index)
        lock = cls.PORT_ADMIN_STATUS_INVERSE['LOCK']
        unlock = cls.PORT_ADMIN_STATUS_INVERSE['UNLOCK']

        cmd_gen = cmdgen.CommandGenerator()

        # lock admin status
        error_indication, error_status, error_index, var_binds = cmd_gen.setCmd(
            cmdgen.CommunityData(snmp_community),
            cmdgen.UdpTransportTarget((dslam_ip, snmp_port),
                                      timeout=snmp_timeout, retries=2),

            (target_oid, rfc1902.Integer(lock))
        )

        # Check for errors and print out results
        if error_indication:
            raise Exception(error_indication)
        else:
            if error_status:
                Exception('%s at %s' % (
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or '?'
                ))

        # unlock admin status
        error_indication, error_status, error_index, var_binds = cmd_gen.setCmd(
            cmdgen.CommunityData(snmp_community),
            cmdgen.UdpTransportTarget((dslam_ip, snmp_port),
                                      timeout=snmp_timeout, retries=2),

            (target_oid, rfc1902.Integer(unlock))
        )
        if error_indication:
            raise Exception(error_indication)
        else:
            if error_status:
                Exception('%s at %s' % (
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or '?'
                ))

        print('reset port admin status')
        return True

        # time.sleep(5)

    @classmethod
    def change_port_line_profile(cls, dslam_info, port_index, lineprofile):
        # port_index = cls.resolve_port_name(dslam, port_name)
        snmp_community = dslam_info['set_snmp_community']
        dslam_ip = dslam_info['ip']
        snmp_port = int(dslam_info.get('snmp_port', 161))
        snmp_timeout = int(dslam_info.get('snmp_timeout', 5))

        target_oid = '.{0}.{1}'.format(cls.PORT_DETAILS_OID_TABLE_INVERSE['LINE_PROFILE'], port_index)

        cmd_gen = cmdgen.CommandGenerator()

        error_indication, error_status, error_index, var_binds = cmd_gen.setCmd(
            cmdgen.CommunityData(snmp_community),
            cmdgen.UdpTransportTarget((dslam_ip, snmp_port),
                                      timeout=snmp_timeout, retries=2),

            (target_oid, rfc1902.OctetString(lineprofile))
        )

        # Check for errors and print out results
        if error_indication:
            raise Exception(error_indication)
        else:
            if error_status:
                Exception('%s at %s' % (
                    error_status.prettyPrint(),
                    error_index and var_binds[int(error_index) - 1][0] or '?'
                ))
        return True

    @classmethod
    def execute_command(cls, dslam_info, command, params):
        params['set_snmp_community'] = dslam_info['set_snmp_community']
        params['get_snmp_community'] = dslam_info['get_snmp_community']
        params['snmp_port'] = dslam_info['snmp_port']
        params['snmp_timeout'] = dslam_info['snmp_timeout']
        params['line_profile_oid'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['LINE_PROFILE']
        params['adsl_upstream_snr_oid'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_UPSTREAM_SNR']
        params['adsl_downstream_snr_oid'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_DOWNSTREAM_SNR']
        params['adsl_curr_upstream_oid'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_CURR_UPSTREAM_RATE']
        params['adsl_curr_downstream_oid'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['ADSL_CURR_DOWNSTREAM_RATE']
        params['adsl_outcomming_traffic'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['OUTGOING_TRAFFIC']
        params['adsl_incomming_traffic'] = cls.PORT_DETAILS_OID_TABLE_INVERSE['INCOMING_TRAFFIC']
        command_class = cls.command_factory.get_type(command)(params)
        command_class.HOST = dslam_info['ip']
        command_class.telnet_username = dslam_info['telnet_username']
        command_class.telnet_password = dslam_info['telnet_password']
        return command_class.run_command()
    @classmethod
    def execute_bulk_command(cls, dslams_data, commands, result_filepath, success_filepath, error_filepath, slot_ports):
        for dslam_data in dslams_data:
            ip = dslam_data.get('ip')
            dslam_id = dslam_data.get('id')
            telnet_username = dslam_data.get('telnet_username')
            telnet_password = dslam_data.get('telnet_password')
            result = Zyxel.run_commands(dslam_id, ip, telnet_username, telnet_password, commands, slot_ports)
            print('*****************************************')
            print(result)
            print('*****************************************')
            if result:
                with open(result_filepath, 'ab') as log_file:
                    log_file.write('\r\n\r\n=======================================\r\n\r\n')
                    log_file.write('\r\n\r\nid: {0}, name: {1}, ip: {2}\r\n\r\n'.format(dslam_data.get('id'),
                                                                                        dslam_data.get('name').encode(
                                                                                            'utf-8'),
                                                                                        dslam_data.get('ip')))
                    log_file.write(result + '\n')
                    log_file.write('\r\n\r\n=======================================\r\n\r\r\n')
                with open(success_filepath, 'ab') as success_file:
                    success_file.write(str(dslam_data.get('id')) + ',' + dslam_data.get('ip') + '\r\n')
            else:
                with open(error_filepath, 'ab') as error_file:
                    error_file.write(str(dslam_data.get('id')) + ',' + dslam_data.get('ip') + '\r\n')
        return {'result': 'run dslam bulk command is done'}

    @classmethod
    def run_commands(cls, dslam_id, HOST, user, password, commands, slot_ports):
        try:
            tn = telnetlib.Telnet(HOST)
            tn.write((user + "\r\n").encode('utf-8'))
            tn.write((password + "\r\n").encode('utf-8'))
            time.sleep(1)
            result = tn.read_until('Password:')
            if slot_ports:
                type_dslam_port, slot_port_objs = slot_ports
                if type_dslam_port == 'slot':
                    for slot in slot_port_objs:
                        for command in commands:
                            template_tags = command.get('command_template').split(',')
                            try:
                                for template_tag in template_tags:
                                    template_tag_value = command.get('params')
                                    template_tag_value.update({'slot_number': slot})
                                    tn.write(template_tag.format(**template_tag_value) + '\r\n\r\n'.encode('utf-8'))
                            except Exception as ex:
                                print(('run_commands (slot section) =>>>', ex))
                else:
                    for port in slot_port_objs[dslam_id]:
                        for command in commands:
                            template_tags = command.get('command_template').split(',')
                            try:
                                for template_tag in template_tags:
                                    template_tag_value = command.get('params')
                                    template_tag_value.update(
                                        {'port_number': port['port_number'], 'slot_number': port['slot_number']})
                                    tn.write((template_tag.format(**template_tag_value) + '\r\n\r\n').encode('utf-8'))
                                    time.sleep(1)
                            except Exception as ex:
                                print(('run_commands (port section) =>>>', ex))
            else:
                for command in commands:
                    if bool(command.get('params')):
                        template_tags = command.get('command_template').split(',')
                        template_tag_value = command.get('params')
                        try:
                            for template_tag in template_tags:
                                command = (template_tag.format(**template_tag_value) + '\r\n\r\n').encode('utf-8')
                                tn.write(command)
                                time.sleep(1)
                        except Exception as ex:
                            print(('run_commands (dslam section) =>>>', ex))
                    else:
                        tn.write(command.get('text') + '\r\n\r\n'.encode('utf-8'))
                    time.sleep(1)

            tn.write("end\r\n")
            result = tn.read_until('end')
            tn.write("exit\r\n")
            tn.write("y\r\n")
            tn.close()
            results = result.split('\n')
            results = '\n'.join(results[3:len(results) - 2])
            return results
        except Exception as ex:
            print('---------------------')
            print(ex)
            print((HOST + ',' + user + ',' + password))
            print('---------------------')
            return None

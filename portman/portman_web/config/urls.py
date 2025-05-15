
"""portman_web URL Configuration
"""
from django.conf.urls import include, url
from django.urls import path
from django.contrib import admin
from rest_framework_nested import routers
from django.conf import settings
import django

from dslam.views import *
from users.views import *
from router.views import *
from switch.views import *
from contact.views import *
from radio.views import *
from olt.views import *
from cloud.views import *
from filemanager.views import *
from zabbix.views import *
from modem.views import GetModemInfoAPIView
from adminplus.sites import AdminSitePlus
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_swagger.views import get_swagger_view
from lte.views import *
from cartable.views import *
from knowledge_graph.views import *
from ngn.views import *

admin.site = AdminSitePlus()
admin.site.site_title = 'PortMan Admin'
admin.site.site_header = 'Portman Admin Panel'
admin.site.index_title = 'System Administration'
admin.autodiscover()

schema_view = get_swagger_view(title='Pastebin API')

# Router
portman_router = routers.SimpleRouter()
portman_router.register(r'permission/profiles', PermissionProfileViewSet, basename='permission-profile')
portman_router.register(r'permission', PermissionViewSet, basename='permission')
portman_router.register(r'permission-profile', PermissionProfilePermissionViewSet, basename='permission-profile-permission')
portman_router.register(r'users/installers', InstallersViewSet, basename='installers')
portman_router.register(r'users/permission-profile', UserPermissionProfileViewSet, basename='user-permission-profile')
portman_router.register(r'users/notifications/contact-group', ContactGroupViewSet, basename='contact-group')
portman_router.register(r'users/notifications/notifiable-users', NotifiableUsersViewSet, basename='contacts')
portman_router.register(r'users/notifications/logs', ShowNotificationLogViewSet, basename='notification-log')
portman_router.register(r'users/province-access', ProvinceAccessViewSet, basename='province-access')
portman_router.register(r'users', UserViewSet, basename='users')
portman_router.register(r'users/auditlog', UserAuditLogViewSet, basename='user-audit-log')
portman_router.register(r'mdfdslam', MDFDSLAMViewSet, basename='mdfdslam')
portman_router.register(r'dslam/bulk-command/result', DSLAMBulkCommandResultViewSet, basename='dslam-bulk-command-result')
portman_router.register(r'dslam/dslam-type', DSLAMTypeViewSet, basename='dslam-type')
portman_router.register(r'dslam/cart', DSLAMCartViewSet, basename='dslam')
portman_router.register(r'dslam/location', DSLAMLocationViewSet, basename='dslam-location')
portman_router.register(r'dslam/faulty-config', DSLAMFaultyConfigViewSet, basename='dslam-faulty-config')
portman_router.register(r'dslam/command/result', DSLAMCommandViewSet, basename='dslam-command')
portman_router.register(r'dslam/events', DSLAMEventViewsSet, basename='dslam-event')
portman_router.register(r'lineprofile', LineProfileViewSet, basename='line-profile')
portman_router.register(r'dslam', DSLAMViewSet, basename='dslam')
portman_router.register(r'dslamport/faulty', DSLAMPortFaultyViewSet, basename='dslam-port-faulty')
portman_router.register(r'dslamport/events', DSLAMPortEventViewsSet, basename='dslam-port-event')
portman_router.register(r'dslamport/vlan', DSLAMPortVlanViewSet, basename='dslam-port-vlan')
portman_router.register(r'telecom-center/mdf', TelecomCenterMDFViewSet, basename='telecom_center_mdf')
portman_router.register(r'telecom-center/location', TelecomCenterLocationViewSet, basename='telecom-center-location')
portman_router.register(r'telecom-center', TelecomCenterViewSet, basename='telecom-center')
portman_router.register(r'dslam-port', DSLAMPortViewSet, basename='dslam-port')
portman_router.register(r'dslam-port-snapshot', DSLAMPortSnapshotViewSet, basename='dslam-port-snapshot')
portman_router.register(r'vlan', VlanViewSet, basename='vlan')
portman_router.register(r'reseller', ResellerViewSet, basename='reseller')
portman_router.register(r'customer-port', CustomerPortViewSet, basename='customer-port')
portman_router.register(r'port-command', PortCommandViewSet, basename='port-command')
portman_router.register(r'command', CommandViewSet, basename='command')
portman_router.register(r'city/location', CityLocationViewSet, basename='city-location')
portman_router.register(r'city', CityViewSet, basename='city')
portman_router.register(r'reseller-port', ResellerPortViewSet, basename='reseller-port')
portman_router.register(r'terminal', TerminalViewSet, basename='terminal')
portman_router.register(r'router', RouterViewSet, basename='router')
portman_router.register(r'switch', SwitchViewSet, basename='switch')
portman_router.register(r'switch-command', SwitchCommandViewSet, basename='switch_command')
portman_router.register(r'router-command', RouterCommandViewSet, basename='router_command')
portman_router.register(r'contact/portmap', PortMapViewSet, basename='contact')
portman_router.register(r'radio', RadioViewSet, basename='radio')
portman_router.register(r'radio-command', RadioCommandViewSet, basename='radio-command')
portman_router.register(r'portman-log', PortmanLogViewSet, basename='portman-log')
portman_router.register(r'farzanegan_data', FarzaneganViewSet, basename='farzanegan_data')
portman_router.register(r'pishgaman-note', GetNotesViewSet, basename='notes')
portman_router.register(r'dslamport/dslam-port-snapshot', DSLAMPortSnapshotViewSet, basename='port-snapshot')
portman_router.register(r'portman-commands-log', PortmanCommandsLoggingViewSet, basename='portman-commands-log')
portman_router.register(r'ftth/olt/commands', OLTCommandViewSet, basename='olt-commands')
portman_router.register(r'ftth/olt/(?P<olt_id>\d+)/cards', OltCardViewSet, basename='olt-card')
portman_router.register(r'ftth/olt/(?P<olt_id>\d+)/card/(?P<card_number>\d+)/ports', OltPortViewSet, basename='olt-port')
portman_router.register(r'ftth/olt', OLTViewSet, basename='olt')
portman_router.register(r'Location_services_log', GetDatatLocationsLoggingViewSet, basename='Location_services_log')
portman_router.register(r'ngn-device', NgnDeviceViewSet, basename='ngn-device')
portman_router.register(r'ftth/cabinet', OLTCabinetViewSet, basename='cabinet')
portman_router.register(r'ftth/odc', ODCViewSet, basename='ODC')
portman_router.register(r'ftth/odc-type', OdcTypeViewSet, basename='odc-type')
portman_router.register(r'ftth/cabinet-type', OLTCabinetTypeViewSet, basename='cabinet-type')
portman_router.register(r'ftth/fat', FATViewSet, basename='fat')
portman_router.register(r'ftth/splitter', SplitterViewSet, basename='splitter')
portman_router.register(r'ftth/ont', OntViewSet, basename='ont')
portman_router.register(r'ftth/ont-setup', OntSetupViewSet, basename='ont-setup')
portman_router.register(r'ftth/user', OLTUserViewSet, basename='user')
portman_router.register(r'ftth/fat-type', FatTypeViewSet, basename='fat-type')
portman_router.register(r'ftth/microduct-type', MicroductTypeViewSet, basename='microduct-type')
portman_router.register(r'ftth/splitter-type', SplitterTypeViewSet, basename='splitter-type')
portman_router.register(r'ftth/ont-type', OntTypeViewSet, basename='ont-type')
portman_router.register(r'ftth/atb-type', AtbTypeViewSet, basename='atb-type')
portman_router.register(r'ftth/cable-type', CableTypeViewSet, basename='cable-type')
portman_router.register(r'ftth/olt-type', OLTTypeViewSet, basename='olt-type')
portman_router.register(r'ftth/handhole', HandholeViewSet, basename='handhole')
portman_router.register(r'ftth/t', HandholeViewSet, basename='T')
portman_router.register(r'ftth/handhole-type', HandholeTypeViewSet, basename='handhole-type')
portman_router.register(r'ftth/handhole-relation', HandholeRelationViewSet, basename='handhole-relation')
portman_router.register(r'ftth/joint', JointViewSet, basename='joint')
portman_router.register(r'ftth/joint-type', JointTypeViewSet, basename='joint-type')
portman_router.register(r'cloud/config-request', ConfigRequestViewSet, basename='cloud-config-request')
portman_router.register(r'cloud/devices', DeviceViewSet, basename='cloud-devices')
portman_router.register(r'ftth/microduct', MicroductViewSet, basename='microduct')
portman_router.register(r'ftth/cable', CableViewSet, basename='cable')
portman_router.register(r'ftth/building', BuildingViewSet, basename='building')
portman_router.register(r'ftth/terminal', TerminalViewSet, basename='terminal')
portman_router.register(r'ftth/routes', RoutesViewSet, basename='ftth-routes')
portman_router.register(r'ftth/reserved-port', ReservedPortsViewSet, basename='ftth-reserved-ports')
microduct_router = routers.NestedDefaultRouter(portman_router, r'ftth/microduct', lookup='microduct')
microduct_router.register('cables', MicroductsCablesViewSet, basename='microduct-cables')
joint_router = routers.NestedDefaultRouter(portman_router, r'ftth/joint', lookup='joint')
joint_router.register('cables', JointsCablesViewSet, basename='joint-cables')
terminalPorts_router = routers.NestedDefaultRouter(portman_router, r'ftth/terminal', lookup='terminal')
terminalPorts_router.register('ports', TerminalPortViewSet, basename='terminal-ports')
portman_router.register(r'technical-profile', TechnicalProfileViewSet, basename='technical-profile')
portman_router.register(r'technical-user', TechnicalUserViewSet, basename='technical-user')
portman_router.register(r'filemanger', FileViewSet, basename='filamanger')
portman_router.register(r'ftth/chart', FtthTreeViewSet, basename='ftth-chart')
portman_router.register(r'lte/map/points', MapPointViewSet, basename='lte-map-points')
portman_router.register(r'ftth/patch-cord-type', PatchCordTypeTypeViewSet, basename='patch-cord-type')
portman_router.register(r'ftth/inspection', InspectionViewSet, basename='inspection')

portman_router.register(r'cartable/ticket', TicketViewSet, basename='cartable_ticket')
portman_router.register(r'cartable/ticket/(?P<ticket_id>\d+)/poll', PollViewSet, basename='cartable_poll')
portman_router.register(r'cartable/ticket/(?P<ticket_id>\d+)/tasklist', CartableTaskListViewSet, basename='ticket_tasklist')
portman_router.register(r'cartable/ticket/(?P<ticket_id>\d+)/reminder', ReminderViewSet, basename='reminder')
portman_router.register(r'cartable/ticket/(?P<ticket_id>\d+)/tasklist/(?P<task_list_id>\d+)/task', CartableTaskViewSet, basename='ticket_task')
portman_router.register(r'cartable/ticket-type', TicketTypeViewSet, basename='cartable_ticket_type')

portman_router.register(r'knowledge-graph/call', CallViewSet, basename='call')
portman_router.register(r'knowledge-graph/(?P<knowledge_graph_id>\d+)/subgraph/(?P<subgraph_id>\d+)/node', NodeViewSet, basename='node')
portman_router.register(r'knowledge-graph/(?P<knowledge_graph_id>\d+)/subgraph/(?P<subgraph_id>\d+)/edge', EdgeViewSet, basename='edge')
portman_router.register(r'knowledge-graph/(?P<knowledge_graph_id>\d+)/subgraph', SubgraphViewSet, basename='subgraph')
portman_router.register(r'knowledge-graph', KnowledgeGraphViewSet, basename='knowledge_graph')

portman_router.register(r'ngn/blocked-list/mobile-number', MobileNumberViewSet, basename='blocked_list_mobile_number')
portman_router.register(r'ngn/blocked-list/advertiser', AdvertiserViewSet, basename='blocked_list_advertiser')
portman_router.register(r'ngn/blocked-list', BlockedListViewSet, basename='blocked_list')

urlpatterns = [
    url(r'^users/get-token', obtain_jwt_token),
    url(r'^apis-doc/v1/', schema_view),
    url(r'/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/users/notifications/send-message/$', SendMessageApiView.as_view(), name='send-message-to-users'),
    url(r'^api/v1/dslamport/register-port/$', AddToVlanAPIView.as_view(), name='register-port'),
    # url(r'^api/v1/dslamport/register-port/$', RegisterPortAPIView.as_view(), name='register-port'),
    #url(r'^api/v1/dslamport/run-command/$', RunCommandAPIView.as_view(), name='run-command'),
    url(r'^api/v1/dslamport/port-status-report/$', PortStatusReportView.as_view(), name='port-status-report'),
    url(r'^api/v1/dslamport/port-info/$', GetPortInfoView.as_view(), name='get-port-info'),
    url(r'^api/v1/dslamport/port-admin-status/$', ChangePortAdminStatusView.as_view(), name='change-port-admin-status'),
    url(r'^api/v1/dslamport/reset-admin-status/$', ResetAdminStatusView.as_view(), name='reset-admin-status'),
    url(r'^api/v1/dslamport/port-line-profile/$', ChangePortLineProfileView.as_view(), name='change-port-line-profile'),
    url(r'^api/v1/dslamport/UpdateBukht/$', BukhtUpdateAPIView.as_view(), name='Bukht-Update'),
    url(r'^api/v1/dslamport/getFreePortInfo/$', GetFreePortInfoAPIView.as_view(), name='Get-Free-Port-Info'),
    url(r'^api/v1/dslamport/command/$', DSLAMPortRunCommandView.as_view(), name='dslam-port-run-command'),
    url(r'^api/v1/dslamport/command2/$', DSLAMPortRunCommand2View.as_view(), name='dslam-port-run-command'),
    url(r'^api/v1/dslamport/free-Port/$', FreePortAPIView.as_view(), name='freePort'),
    url(r'^api/v1/dslamport/reserve-Port/$', ReservePortAPIView.as_view(), name='reservePort'),
    url(r'^api/v1/dslamport/Add-Customer/$', AddCustomerAPIView.as_view(), name='addCustomer'),
    url(r'^api/v1/dslamport/port-Assign/$', PortAssignAPIView.as_view(), name='portAssign'),
    url(r'^api/v1/dslamport/getBukhtInfo/$', GetBukhtInfoAPIView.as_view(), name='getBukhtInfo'),
    url(r'^api/v1/dslamport/getProvinces/$', GetProvincesAPIView.as_view(), name='getProvinces'),
    url(r'^api/v1/dslamport/getCities/$', GetCitiesAPIView.as_view(), name='getCities'),
    url(r'^api/v1/dslamport/getTelecomCenters/$', GetTelecomCentersAPIView.as_view(), name='getTelecomCenters'),
    url(r'^api/v1/dslamport/getDslams/$', GetDslamsAPIView.as_view(), name='getDslams'),
    url(r'^api/v1/dslamport/getUserPortInfo/$', GetUserPortInfoAPIView.as_view(), name='getUserPortInfo'),
    url(r'^api/v1/dslamport/getCommandInfoSnmp/$', GetCommandInfoSnmp.as_view(), name='getCommandInfoSnmp'),
    url(r'^api/v1/dslamport/getCommandInfoTelnet/$', GetCommandInfoTelnet.as_view(), name='getCommandInfoTelnet'),
    url(r'^api/v1/dslamport/getPortInfoByUsername/$', GetPortInfoByUserNameAPIView.as_view(), name='getPortInfoByUsername'),
    url(r'^api/v1/dslamport/registerPortByResellerId/$', RegisterPortByResellerIdAPIView.as_view(), name='registerPortByResellerId'),
    url(r'^api/v1/dslamport/getAllFreePorts/$', GetAllFreePortsAPIView.as_view(), name='getAllFreePortsAPI'),
    url(r'^api/v1/dslamport/changeBukht/$', ChangeBukhtAPIView.as_view(), name='changeBukht'),
    url(r'^api/v1/dslamport/getPortHistory/$', GetPortHistoryAPIView.as_view(), name='getPortHistory'),
    url(r'^api/v1/dslamport/getDslamBackup/$', GetDslamBackupAPIView.as_view(), name='getDslamBackup'),
    url(r'^api/v1/dslamport/showDslamBackups/$', ShowDslamBackups.as_view(), name='showDslamBackups'),
    url(r'^api/v1/dslamport/downloadDslamBackups/$', DownloadDslamBackupFileAPIView.as_view(), name='downloadDslamBackups'),
    url(r'^api/v1/dslamport/SendMail/$', SendMailAPIView.as_view(), name='SendMail'),
    url(r'^api/v1/dslamport/getPortInfoById/$', GetPortInfoByIdAPIView.as_view(), name='getPortInfoById'),
    #url(r'^api/v1/dslamport/fiberHomeCommand/$', FiberHomeCommandAPIView.as_view(), name='fiberHomeComman'),
    url(r'^api/v1/dslamport/run-command/$', FiberHomeCommandAPIView.as_view(), name='fiberHomeComman'),
    url(r'^api/v1/dslamport/dslam_commandsV2/$', DslamCommandsV2APIView.as_view(), name='fiberHomeComman'),
    url(r'^api/v1/dslamport/runCommandByIP/$', RunCommandByIPAPIView.as_view(), name='runCommandByIP'),
    url(r'^api/v1/dslamport/bitstreamFreePort/$', BitstreamFreePortAPIView.as_view(), name='bitstreamFreePort'),
    url(r'^api/v1/dslamport/getDslamBackupByIdAPIView/$', GetDslamBackupByIdAPIView.as_view(), name='getDslamBackupByIdAPIView'),
    url(r'^api/v1/dslamport/updateProfile/$', UpdateProfileAPIView.as_view(), name='updateProfile'),
    url(r'^api/v1/dslamport/setTimeAllDslams/$', SetTimeAllDslamsAPIView.as_view(), name='setTimeAPIView'),
    url(r'^api/v1/dslamport/getPortDownstream/$', GetPortDownstreamAPIView.as_view(), name='getPortDownstreamAPIView'),
    url(r'^api/v1/dslamport/saveLineStats/$', SaveLineStatsAPIView.as_view(), name='saveLineStats'),
    url(r'^api/v1/dslamport/getSeltByFqdn/$', GetSeltByFqdnAPIView.as_view(), name='getSeltByFqdn'),
    url(r'^api/v1/dslamport/get_snmp_port_status/$', GetSNMPPortStatusAPIView.as_view(), name='get_snmp_port_status'),
    url(r'^api/v1/dslamport/get_snmp_port_traffic/$', GetSNMPPortTrafficAPIView.as_view(), name='get_snmp_port_traffic'),

    # url(r'^api/v1/dslamport/createTicket/$', CreateTicketAPIView.as_view(), name='createTicket'),
    # url(r'^api/v1/dslamport/getticket/$', GetTicketInfoAPIView.as_view(), name='getticket'),
    url(r'^api/v1/dslamport/port_conflict_correction/$', PortConflictCorrectionAPIView.as_view(), name='port_conflict_correction'),
    url(r'^api/v1/dslamport/addTicket/$', AddTicketDanaAPIView.as_view(), name='addTicket'),
    url(r'^api/v1/dslamport/get_ticket_Details/$', GetTicketDetailsDanaAPIView.as_view(), name='get_ticket_Details'),
    url(r'^api/v1/dslamport/get_hosts_from_zabbix/$', GetHostsFromZabbixAPIView.as_view(), name='get_hosts_from_zabbix'),
    url(r'^api/v1/dslamport/check_network_bulk_availability/$', CheckNetworkBulkAvailability.as_view(), name='check_network_bulk_availability'),
    url(r'^api/v1/dslamport/get_hosts_from_zabbix/$', GetHostsFromZabbixAPIView.as_view(), name='get_hosts_from_zabbix'),
    url(r'^api/v1/dslam/get_items_from_zabbix/$', GetItemsFromZabbixAPIView.as_view(), name='get_items_from_zabbix'),
    url(r'^api/v1/dslam/bulk-command/$', BulkCommand.as_view(), name='bulk-command'),
    url(r'^api/v1/dslam/ngn_register/$', NGNRegisterAPIView.as_view(), name='bulk-command'),

    url(r'^api/v1/dslam/get_dslams_packet_loss_count/$', DslamIcmpSnapshotCount.as_view(), name='get_dslams_packet_loss_count'),
    url(r'^api/v1/dslam/get_interface_traffic_input/$', GetInterfaceTrafficInput.as_view(), name='get_interface_traffic_input'),
    url(r'^api/v1/dslam/zabbix_get_history/$', ZabbixGetHistory.as_view(), name='zabbix_get_history'),
    url(r'^api/v1/dslam/get_fifty_five_precntage/$', GetFiftyFivePercent.as_view(), name='get_fifty_five_precntage'),
    url(r'^api/v1/quick-search/$', QuickSearchView.as_view(), name='quick-search'),

    url(r'^api/v1/dslamport/ranjeNumber-Inquiry/$', RanjeNumberInquiryAPIView.as_view(), name='ranjeNumberInquiry'),
    url(r'^api/v1/dslamport/fetch-shaskam-inquiry/$', FetchShaskamInquiryAPIView.as_view(), name='fetchShaskamInquiry'),
    url(r'^api/v1/dslamport/set-shaskam-inquiry/$', SetShaskamInquiryAPIView.as_view(), name='setShaskamInquiry'),
    url(r'^api/v1/dslam/icmp/command/$', DSLAMRunICMPCommandView.as_view(), name='dslam-run-icmp-command'),
    url(r'^api/v1/dslam/icmp_by_fqdn/command/$', DSLAMRunICMPCommandByFqdnView.as_view(), name='icmp_by_fqdn'),
    url(r'^api/v1/dslamport/check_port_conflict/$', CheckPortConflict.as_view(),
        name='check_port_conflict'),
    url(r'^api/v1/dslamport/search_fqdns/$', SearchFqdnsAPIView.as_view(),
        name='search_fqdns'),
    url(r'^api/v1/dslamport/get_dslamport_snapshot/$', GetDslamPortSnapShotAPIView.as_view(),
        name='search_fqdns'),
    url(r'^api/v1/dslam/load_dslam_ports/$', LoadDslamPorts.as_view(), name='load_dslam_ports'),
    url(r'^api/v1/dslamport/get_port_count/$', GetDslamPorts.as_view(), name='get_port_count'),
    url(r'^api/v1/dslamport/fiberhome_get_card/$', FiberHomeGetCardAPIView.as_view(), name='fiberhome_get_card'),
    url(r'^api/v1/dslamport/fiberhome_get_port/$', FiberHomeGetPortAPIView.as_view(), name='fiberhome_get_port'),
    url(r'^api/v1/dslamport/user_status/$', UserStatusAPIView.as_view(), name='user_status'),
    url(r'^api/v1/dslamport/user_mac_address/$', UserMacAddressAPIView.as_view(), name='user_mac_address'),
    url(r'^api/v1/dslamport/partak_user_status/$', PartakUserStatusAPIView.as_view(), name='user_status'),
    url(r'^api/v1/dslamport/upload_rented_port/$', UploadRentedPort.as_view(), name='upload_rented_port'),
    url(r'^api/v1/dslamport/rented_port/$', RentedPortAPIView.as_view(), name='rented_port'),
    url(r'^api/v1/dslamport/get_pvc_vlan/$', GetPVCVlanAPIView.as_view(), name='get_pvc_vlan'),
    url(r'^api/v1/dslamport/add_to_vlan/$', AddToVlanAPIView.as_view(), name='add_to_vlan'),
    url(r'^api/v1/dslamport/add_to_pishgaman/$', AddToPishgamanAPIView.as_view(), name='add_to_pishgaman'),
    url(r'^api/v1/dslamport/portmap/$', PortmapAPIView.as_view(), name='portmap'),
    url(r'^api/v1/dslamport/get-captcha/$', GetCaptchaAPIView.as_view(), name='get-captcha'),
    url(r'^api/v1/dslamport/farzanegan_scrapping/$', FarzaneganScrappingAPIView.as_view(), name='farzanegan_scrapping'),
    url(r'^api/v1/user/get_user_permission_profile_objects/$', GetUserPermissionProfileObjectsAPIView.as_view(),
        name='get_user_permission_profile_objects'),
    url(r'^api/v1/user/set_permission_for_user/$', SetPermissionForUserAPIView.as_view(),
        name='set_permission_for_user'),
    url(r'^api/v1/user/set_permission_by_permission_profile_id/$', SetBulkPermissionByPermissionProfileId.as_view(),
        name='set_permission_by_permission_profile_id'),
    url(r'^api/v1/user/set_bulk_permission_for_user/$', SetBulkPermissionForUserApiView.as_view(),
        name='set_bulk_permission_for_user'),
    url(r'^api/v1/user/delete_bulk_permission_for_user/$', DeleteBulkPermissionForUserApiView.as_view(),
        name='delete_bulk_permission_for_user'),
    url(r'^api/v1/partak/get_partak_provinces/$', GetPartakProvincesAPIView.as_view(),
        name='get_partak_provinces'), \
    url(r'^api/v1/partak/get_partak_cities_by_province_id/$', GetPartakCitiesByProvinceIdAPIView.as_view(),
        name='get_partak_cities_by_province_id'),
    url(r'^api/v1/partak/get_partak_telecoms_by_city_id/$', GetPartakTelecomsByCityIdAPIView.as_view(),
        name='get_partak_telecoms_by_city_id'),
    url(r'^api/v1/partak/get_partak_dslam_list_by_telecom_id/$', GetPartakDslamListByTelecomIdAPIView.as_view(),
        name='get_partak_dslam_list_by_telecom_id'),
    url(r'^api/v1/partak/update_partak_fqdn/$', UpdatePartakFqdnAPIView.as_view(),
        name='update_partak_fqdn'),
    url(r'^api/v1/pishgaman-note/save-note/$', SaveNoteAPIView.as_view(), name='pishgaman-note'),
    url(r'^api/v1/pishgaman-note/(?P<pk>\d+)/change-status/$', GetNotesViewSet.as_view({'patch': 'change_status'}),
        name='change_status'),
    url(r'^api/v1/location-services/$', LocationServicesAPIView.as_view(), name='location-services'),
    url(r'^api/v1/location-services-v2/$', LocationServicesV2APIView.as_view(), name='location-services-v2'),
    url(r'^api/v1/location-services/get_static_locations$', GetStaticLocations.as_view(), name='get_static_locations'),
    # Routers
    # url(r'^api/v1/dslam/icmp_by_fqdn/connect_handler_test/$', ConnectHandlerTest.as_view(),name='connect_handler_test'),
    url(r'^api/v1/router-command/router_run_command/$', RouterRunCommandAPIView.as_view(), name='routerRunCommand'),
    url(r'^api/v1/router/router_run_command/$', RouterRunCommandAPIView.as_view(), name='routerRunCommand'),
    url(r'^api/v1/router/get_router_backup_files_name/$', GetRouterBackupFilesNameAPIView.as_view(),
        name='get_backup_files_name'),
    url(r'^api/v1/router/get_router_uncompleted_backup_file/$', GetUncompletedRoutersBackup.as_view(),
        name='get_router_uncompleted_backup_file'),
    url(r'^api/v1/router/get_router_backup_files_name2/$', GetRouterBackupFilesNameAPIView2.as_view(),
        name='get_backup_files_name'),
    url(r'^api/v1/router/download_router_backup_file/$', DownloadRouterBackupFileAPIView.as_view(), name='download_router_backup_file'),
    url(r'^api/v1/router/get_router_backup_error_file/$', GetRouterBackupErrorFilesNameAPIView.as_view(),
        name='get_router_backup_error_file'),
    url(r'^api/v1/router-command/read_router_backup_error_files_name/$', ReadRouterBackupErrorFilesNameAPIView.as_view(),
        name='read_router_backup_error_files_name'),
    url(r'^api/v1/router/set_ssl_on_router/$', SetSSLOnRouter.as_view(),
        name='set_ssl_on_router'),
    url(r'^api/v1/router/get_router_backup_file_name_with_date/$', GetRouterBackupFileNameWithDate.as_view(),
        name='set_ssl_on_router'),

    # Switches
    url(r'^api/v1/switch/run_command/$', SwitchRunCommandAPIView.as_view(), name='switch_run_command'),
    url(r'^api/v1/switch/get_switch_backup_files_name/$', GetSwitchBackupFilesNameAPIView.as_view(), name='get_switch_backup_files_name'),
    url(r'^api/v1/switch/download_backup_file/$', DownloadBackupFileAPIView.as_view(), name='download_backup_file'),
    url(r'^api/v1/switch/get_backup_error_file/$', GetBackupErrorFilesNameAPIView.as_view(),
        name='get_backup_error_file'),
    url(r'^api/v1/switch/get_backup_error_text/$', GetBackupErrorTextNameAPIView.as_view(),
        name='get_backup_error_file'),
    url(r'^api/v1/switch/read_switch_backup_error_files_name/$', ReadSwitchBackupErrorFilesNameAPIView.as_view(),
        name='read_switch_backup_error_files_name'),
    url(r'^api/v1/switch/get_switch_show_vlan_brief_files_name/$', GetSwitchShowVlanBriefFilesName.as_view(),
        name='get_switch_show_vlan_brief_files_name'),
    url(r'^api/v1/switch/download_view_vlan_brief_file/$', DownloadViewVlanBriefFile.as_view(),
        name='download_view_vlan_brief_file'),

    # Radio
    url(r'^api/v1/radio/get_radio_backup_files_name/$', GetRadioBackupFilesNameAPIView.as_view(),
        name='get_radio_backup_files_name'),

    url(r'^api/v1/radio/download_radio_backup_file/$', DownloadRadioBackupFileAPIView.as_view(),
        name='download_radio_backup_file'),
    url(r'^api/v1/radio/read_radio_backup_error_files_name/$', ReadRadioBackupErrorFilesNameAPIView.as_view(),
        name='download_radio_backup_file'),
    url(r'^api/v1/radio/set_radio_geographical_coordinates/$', SetRadioGeographicalCoordinatesAPIView.as_view(),
        name='set_radio_geographical_coordinates'),

    url(r'^api/v1/contact/get_provinces/$', GetProvincesAPIView.as_view(),
        name='get_provinces'),
    url(r'^api/v1/contact/get_cities_by_province_id/$', GetCitiesByProvinceIdAPIView.as_view(),
        name='get_cities'),
    url(r'^api/v1/contact/get_telecoms_by_city_id/$', GetTelecomsByCityIdAPIView.as_view(),
        name='get_telecoms_by_city_id'),
    url(r'^api/v1/contact/get_port_statuses/$', GetPortsStatus.as_view(),
        name='get_port_statuses'),
    url(r'^api/v1/contact/search_ports/$', SearchPorts.as_view(),
        name='search_ports'),
    url(r'^api/v1/contact/update_status_ports/$', UpdateStatusPorts2.as_view(),
        name='update_status_ports'),
    url(r'^api/v1/contact/get_cities_from_pratak/$', GetCitiesFromPratakAPIView.as_view(),
        name='get_cities_from_pratak'),
    url(r'^api/v1/contact/farzanegan_provider_date/$', FarzaneganProviderDataAPIView.as_view(),
        name='farzanegan_provider_date'),
    url(r'^api/v1/contact/get_ddr_info_exportExcel/$', FarzaneganExportExcelAPIView.as_view(),
        name='get_ddr_info_exportExcel'),
    url(r'^api/v1/user/get_command_result/$', GetCommandHistoryResultAPIView.as_view(), name='get_command_result'),
#portman_cdms
    url(r'^api/v1/portman_cdms/get_user_port_info/$', GetUserPortInfoFromPartakAPIView.as_view(), name='get_user_port_info'),
    url(r'^api/v1/portman_cdms/get_dslam_id_by_fqdn/$', GetDslamIdByFqdnAPIView.as_view(), name='get_dslam_id_by_fqdn'),
    url(r'^api/v1/portman_cdms/get_fqdn_from_zabbix_by_ip/$', GetFqdnFromZabbixByIpAPIView.as_view(), name='get_fqdn_from_zabbix_by_ip'),
    url(r'^api/v1/portman_cdms/get_dslam_id_by_ip/$', GetDSLAMIdByIPAPIView.as_view(),
        name='get_fqdn_from_zabbix_by_ip'),
    url(r'^api/v1/portman_cdms/get_fqdn_from_zabbix/$', GetFqdnFromZabbixAPIView.as_view(),
        name='get_fqdn_from_zabbix_by_ip'),

# FTTH
    url(r'^api/v1/ftth/olt/run_command/$', OLTCommandsAPIView.as_view(), name='run_command'),
    url(r'^api/v1/ftth/olt/ports/saveall/$', BulkSaveOltPortsAPIView.as_view(), name='saveall_olt_ports'),
    url(r'^api/v1/ftth/terminal/ports/saveall/$', BulkSaveTerminalPortsAPIView.as_view(), name='saveall_terminal_ports'),
    url(r'^api/v1/ftth/city/(?P<city_id>\d+)/export-kmz$', CityKMZAPIView.as_view(), name='ExportCityEquipment'),
    url(r'^api/v1/ftth/device_capacity/$', GetDeviceCapacityAPIView.as_view(), name='device_capacity'),
    url(r'^api/v1/ftth/fat/nearest$', FindPointsWithRadiusAPIView.as_view(), name='find_points'),
    url(r'^api/v1/ftth/fat/(?P<pk>\d+)/available_ports/$', FATViewSet.as_view({'get': 'available_ports'}),
        name='fat-available-ports'),
    url(r'^api/v1/ftth/fat/(?P<pk>\d+)/first_port/$', FATViewSet.as_view({'get': 'first_port'}),
        name='first_port'),
    url(r'^api/v1/ftth/splitter/(?P<pk>\d+)/ports/$', SplitterViewSet.as_view({'get': 'ports'}),
        name='splitter-available-ports'),
    url(r'^api/v1/ftth/nearest-equipments/$', NearestEquipmentsAPIView.as_view(), name='nearest-equipments'),
    url(r'^api/v1/ftth/equipment/create_bulk/$', EquipmentCreateBulk.as_view(), name='nearest-equipments'),
    url(r'^api/v1/ftth/approve-objects/$', ApproveObjectsAPIView.as_view(), name='approve_objects_api'),
    url(r'^api/v1/ftth/disapprove-objects/$', DisapproveObjectsAPIView.as_view(), name='disapprove_objects_api'),
    url(r'^api/v1/', include(portman_router.urls)),
    url(r'^api/v1/', include(microduct_router.urls)),
    url(r'^api/v1/', include(joint_router.urls)),
    url(r'^api/v1/', include(terminalPorts_router.urls)),

    url(r'^media/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),

    # NGN Devices
    url(r'^api/v1/ngn-device/get_ngn_device_backup_files_name$', GetNgnDeviceBackupFilesNameAPIView.as_view(),
        name='get_ngn_device_backup_files_name'),
    url(r'^api/v1/ngn-device/download_ngn_device_backup_file$', DownloadNgnDeviceBackupFileAPIView.as_view(),
        name='download_ngn_device_backup_file'),

    # misc
    url(r'^api/v1/misc/postal-code-conversion/$', PostalCodeConversionAPIView.as_view(), name='postal-code-conversion'),
    url(r'^api/v1/misc/farzanegan-job-status/$', FarzaneganJobStatusAPIView.as_view(), name='farzanegan-job-status'),

]



-------------------------router-------------------------------------------------
ALTER SEQUENCE router_router_id_seq RESTART WITH 1;
DELETE FROM router_router;
INSERT INTO "public"."router_router"("device_interfaceid", "host_id", "device_name", "device_ip", "device_fqdn", "router_brand_id", "router_type_id","SSH_password", "SSH_username", "SSH_port", "SSH_timeout", "last_update")
 SELECT DISTINCT 1 as device_interfaceid, zabbix_hosts.id, '' as device_name,zabbix_hosts.device_ip,zabbix_hosts.device_fqdn, router_routergroup.router_brand_id,router_routergroup."id",'eS7*XiMmyeeU'as SSH_password,'mik-backup' as SSH_username, 1001 as SSH_port, 5 as SSH_timeout, NOW() from zabbix_hosts
  LEFT JOIN router_routergroup on router_routergroup.title = zabbix_hosts.device_type
	where (zabbix_hosts.device_fqdn like '%rou%' or zabbix_hosts.device_fqdn like '%core%' or zabbix_hosts.device_type = 'router_board' or zabbix_hosts.device_type = 'router_virtual' or zabbix_hosts.device_type = 'cisco_router') and router_routergroup.title is not NULL and device_fqdn not ilike '%OLD%' and device_fqdn not ilike '%nobkp%' ORDER BY zabbix_hosts.device_ip;
-------------------------router-------------------------------------------------


-------------------------switch-------------------------------------------------
 ALTER SEQUENCE switch_switch_id_seq RESTART WITH 1;
 DELETE from switch_switch;
 INSERT INTO "public"."switch_switch"( "device_interfaceid", "host_id", "device_name", "device_ip", "device_fqdn", "Switch_brand_id", "Switch_type_id", "SSH_password", "SSH_username", "SSH_port", "SSH_timeout","last_update")
 SELECT DISTINCT 2 as device_interfaceid, zabbix_hosts.id ,'' as device_name,zabbix_hosts.device_ip,zabbix_hosts.device_fqdn, switch_switchgroup.switch_brand_id,switch_switchgroup."id",'pP78U@87aJK'as SSH_password,'backup-noc' as SSH_username, 22 as SSH_port, 5 as SSH_timeout , NOW() from zabbix_hosts
  LEFT JOIN switch_switchgroup on switch_switchgroup.title = zabbix_hosts.device_type
where zabbix_hosts.device_fqdn like '%swi%' and switch_switchgroup.title is not NULL and device_fqdn not ilike '%OLD%' and device_fqdn not ilike '%nobkp%' ORDER BY zabbix_hosts.device_ip;

INSERT INTO "public"."switch_switch"( "device_interfaceid", "host_id", "device_name", "device_ip", "device_fqdn", "Switch_brand_id", "Switch_type_id", "SSH_password", "SSH_username", "SSH_port", "SSH_timeout","last_update")
 SELECT DISTINCT 2 as device_interfaceid, zabbix_hosts.id, '' as device_name,zabbix_hosts.device_ip,zabbix_hosts.device_fqdn, switch_switchgroup.switch_brand_id,switch_switchgroup."id",'pP78U@87aJK'as SSH_password,'backup-noc' as SSH_username, 22 as SSH_port, 5 as SSH_timeout, NOW() from zabbix_hosts
  LEFT JOIN switch_switchgroup on switch_switchgroup.title = zabbix_hosts.device_type
where switch_switchgroup.title is not NULL and device_fqdn not ilike '%OLD%' and device_fqdn not ilike '%nobkp%' and device_type = 'switch_layer3' ORDER BY zabbix_hosts.device_ip;

-------------------------switch-------------------------------------------------


-------------------------radio-------------------------------------------------
 ALTER SEQUENCE radio_radio_id_seq RESTART WITH 1;
 DELETE from radio_radio;
 INSERT INTO "public"."radio_radio"( "device_interfaceid", "host_id", "device_name", "device_ip", "device_fqdn", "radio_brand_id", "radio_type_id", "SSH_password", "SSH_username", "SSH_port", "SSH_timeout")
 SELECT DISTINCT 3 as device_interfaceid,zabbix_hosts.id, '' as device_name,zabbix_hosts.device_ip,zabbix_hosts.device_fqdn, radio_radiogroup.radio_brand_id,radio_radiogroup."id",'eS7*XiMmyeeU'as SSH_password,'mik-backup' as SSH_username, 22 as SSH_port, 5 as SSH_timeout from zabbix_hosts
  LEFT JOIN radio_radiogroup on radio_radiogroup.title = zabbix_hosts.device_type
	where radio_radiogroup.title is not NULL and device_fqdn not ilike '%OLD%' and device_fqdn not ilike '%nobkp%' ORDER BY zabbix_hosts.device_ip;
-------------------------radio-------------------------------------------------

------------------------- >> NGN DEVICES -- VOIP-------------------------------------------------
ALTER SEQUENCE router_ngndevice_id_seq RESTART WITH 1;
DELETE from router_ngndevice;

INSERT INTO "public"."router_ngndevice"("device_interfaceid", "host_id", "device_name", "device_ip", "device_fqdn", "router_brand_id", "router_type_id","SSH_password", "SSH_username", "SSH_port", "SSH_timeout", "last_update")
 SELECT DISTINCT 1 as device_interfaceid,zabbix_hosts.id, zabbix_hosts.device_fqdn as device_name,zabbix_hosts.device_ip,zabbix_hosts.device_fqdn, 1 as router_brand_id, 3 as router_type_id, 'YdUxPv7Ja4znrE' as SSH_password,'IT-BackUP' as SSH_username, 22 as SSH_port, 5 as SSH_timeout, NOW() from zabbix_hosts
  LEFT JOIN router_routergroup on router_routergroup.title = zabbix_hosts.device_type
	where zabbix_hosts.device_type = 'ngn_device' and device_fqdn not ilike '%OLD%' and device_fqdn not ilike '%nobkp%' ORDER BY zabbix_hosts.device_ip;
------------------------- << NGN DEVICES -- VOIP-------------------------------------------------

--------------------------------------------- SETTING PASSWORDS ------------------------------
-- Infrastructure Group
UPDATE "public"."switch_switch" set "SSH_password" = 'GXp)@R$s8^)D^qT!', "SSH_username" = 'Portman-OSS' 
WHERE host_id in (SELECT zh.id from zabbix_hosts zh left join zabbix_hostgroups zhg ON zh.host_group_id = zhg.id where zhg.group_name ilike '%Infrastructure%');

UPDATE "public"."router_router" set "SSH_password" = 'GXp)@R$s8^)D^qT!', "SSH_username" = 'Portman-OSS' 
WHERE host_id in (SELECT zh.id from zabbix_hosts zh left join zabbix_hostgroups zhg ON zh.host_group_id = zhg.id where zhg.group_name ilike '%Infrastructure%');

-- VOIP-NGN Group
UPDATE "public"."router_ngndevice" set "SSH_password" = 'YdUxPv7Ja4znrE', "SSH_username" = 'IT-BackUP'
WHERE host_id in (SELECT zh.id from zabbix_hosts zh left join zabbix_hostgroups zhg ON zh.host_group_id = zhg.id where zhg.group_name ilike '%Voip-NGN%');

-------------------------portman_zabbix_hosts-------------------------------------------------
--ALTER SEQUENCE portman_zabbix_hosts_id_seq RESTART WITH 2526;

--DELETE FROM portman_zabbix_hosts;

--INSERT INTO "public"."portman_zabbix_hosts"("host_id", "device_group", "device_ip", "device_fqdn", "last_updated", "device_type", "device_brand")

--select "host_id", "device_group", "device_ip", "device_fqdn", "last_updated", "device_type", "device_brand" from zabbix_hosts;
-------------------------portman_zabbix_hosts-------------------------------------------------
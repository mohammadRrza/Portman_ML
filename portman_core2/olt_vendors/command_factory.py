class CommandFactory:
    def __init__(self):
        self.__resource_types = {} #name:class

    def clear(self):
        self.__resource_types = {}

    def register_type(self, name, klass):
        if name in self.__resource_types:
            raise Exception(f'Resource Type "{name}" Already Registered!')
        self.__resource_types[name] = klass

    def get_type(self, name):
        if name in self.__resource_types:
            return self.__resource_types[name]
        raise Exception('Resource Type "%s" is Not Registered!'%name)

    def make_command(self, oltInfo, command, params):
        params['set_snmp_community'] = oltInfo['set_snmp_community']
        params['get_snmp_community'] = oltInfo['get_snmp_community']
        params['snmp_port'] = oltInfo['snmp_port']
        params['snmp_timeout'] = oltInfo['snmp_timeout']
        params['olt_vlan_number'] = oltInfo['vlan_number']
        params['olt_gemport'] = oltInfo['gemport']
        params['olt_inbound_index'] = oltInfo['inbound_index']
        params['olt_outbound_index'] = oltInfo['outbound_index']
        params['olt_mg_id'] = oltInfo['mg_id']
        params['olt_ont_port_id'] = oltInfo['ont_port_id']
        params['olt_priority'] = oltInfo['priority']
        params['olt_profile_id'] = oltInfo['profile_id']
        command_class = self.get_type(command)(params)
        command_class.HOST = oltInfo['ip']
        command_class.telnet_username = oltInfo['telnet_username']
        command_class.telnet_password = oltInfo['telnet_password']
        return command_class


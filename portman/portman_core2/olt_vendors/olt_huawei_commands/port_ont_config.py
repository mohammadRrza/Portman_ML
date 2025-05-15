from .base_command import BaseCommand

class PortOntConfig(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        #self.simulate = True

        vlanNumber = params.get('custom_vlan_number')
        if vlanNumber == "":
            vlanNumber = params.get('olt_vlan_number')

        gemPort = params.get('gemport')
        if gemPort == "":
            gemPort = params.get('olt_gemport')

        self.command_str = "service-port vlan {0} gpon 0/{1}/{2} ont {3} gemport {4} multi-service user-vlan {5} tag-transform translate inbound traffic-table index {6} outbound traffic-table index {7}\r\n\r\n".format(
            vlanNumber,
            self.port_indexes['slot_number'],
            self.port_indexes['port_number'],
            params.get('ont'),
            gemPort,
            vlanNumber,
            params.get('olt_inbound_index'),
            params.get('olt_outbound_index'),
        )
        self.error_list = ["Failure: The traffic table does not exist"]



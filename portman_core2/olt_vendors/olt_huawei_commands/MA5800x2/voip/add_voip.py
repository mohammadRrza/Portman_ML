from ...base_command import BaseCommand

class AddVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.command_str = "__"
        self.commands = [
            #ont ipconfig <P> <O> ip-index 0 dhcp vlan <VlanID>
            "ont ipconfig {0} {1} ip-index 0 dhcp vlan {2}\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                params.get('olt_vlan_number')
            ),
            #if-sip add <P> <O> 1 ip-index 0 sipagent-profile profile-id 1
            "if-sip add {0} {1} 1 ip-index 0 sipagent-profile profile-id 1\r\n\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont')
            ),
            #sippstnuser add <PortID> <OntID> 1 mgid 1 username <number> password <password> telno <number>
            "sippstnuser add {0} {1} 1 mgid 1 username {2} password {3} telno {4}\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                #params.get('olt_ont_port_id', 1),
                #params.get('olt_mg_id', 1),
                params.get('username'),
                params.get('password'),
                params.get('telno'),
            )
        ]
        #self.error_list = ["Failure: The MG ID is already used"]

    def fetch_command_output(self):

        end_str = bytes(self.get_end_str(), 'utf-8')

        output = ""
        for command in self.commands:
            self.command_str = command
            self.tn.write(bytes(self.command_str, 'utf-8'))
            result = self.tn.read_until(end_str, 2)
            output += str(result)

        return self.set_command_output(output)

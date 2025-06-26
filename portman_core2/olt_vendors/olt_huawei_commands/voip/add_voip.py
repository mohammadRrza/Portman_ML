from ..base_command import BaseCommand

class AddVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.command_str = "__"
        self.commands = [
            "ont ipconfig {0} {1} ip-index 1 dhcp vlan {2} priority {3}\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                params.get('olt_vlan_number'),
                params.get('olt_priority')
            ),
            "if-sip add {0} {1} {2} proxy-server 172.28.238.162 outbound-server 172.28.238.162 ip-index 1\r\n\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                params.get('olt_mg_id')
            ),
            "sippstnuser add {0} {1} {2} mgid {3} username {4} password {5} telno {6}\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                params.get('olt_ont_port_id'),
                params.get('olt_mg_id'),
                params.get('username'),
                params.get('password'),
                params.get('telno'),
            ),
            "\r\n\r\n"
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

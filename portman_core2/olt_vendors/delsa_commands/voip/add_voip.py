from ..base_command import BaseCommand

class AddVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.command_str = "__"
        self.gpon_mode = True
        self.commands = [
            "ont ipconfig {0} ip-index 1 dhcp vlan {1}\r\n\r\n\r\n".format(
                params.get('ont'),
                params.get('olt_vlan_number')
            ),
            "ont sipconfig {0} ip-index 1 port_id {1} username {2} password {3} phone {4} ont-sipprofile-id {5}\r\n\r\n".format(
                params.get('ont'),
                params.get('pot_port_id', params.get('olt_ont_port_id', 1)),
                params.get('username'),
                params.get('password'),
                params.get('telno'),
                params.get('olt_profile_id'),
            ),
            "exit\r\n\r\n"
            "save\r\n"
        ]
        self.error_list = ["Error, Ont sip config fail"]

    def fetch_command_output(self):

        end_str = bytes(self.get_end_str(), 'utf-8')

        output = ""
        for command in self.commands:
            self.command_str = command
            self.tn.write(bytes(self.command_str, 'utf-8'))
            result = self.tn.read_until(end_str, 2)
            output += str(result)

        return self.set_command_output(output)

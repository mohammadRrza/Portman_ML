from ..base_command import BaseCommand


class DeleteVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = "__"

        self.commands = [
            "sippstnuser del {0} {1} pots {2}\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                params.get('olt_ont_port_id')
            ),
            "if-sip del {0} {1} {2}\r\n\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
                params.get('olt_mg_id')
            ),
            "undo ont ipconfig {0} {1}\r\n\r\n".format(
                self.port_indexes['port_number'],
                params.get('ont'),
            )
        ]

        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.error_list = ["Failure: The user does not exist"]
        self.success_message = "Voip Deleted Successfully"

    def fetch_command_output(self):

        print(self.commands)
        end_str = bytes(self.get_end_str(), 'utf-8')

        output = ""
        for command in self.commands:
            self.command_str = command
            self.tn.write(bytes(self.command_str, 'utf-8'))
            result = self.tn.read_until(end_str, 2)
            output += str(result)

        return self.set_command_output(output)

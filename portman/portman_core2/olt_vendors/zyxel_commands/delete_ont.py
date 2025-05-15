from .base_command import BaseCommand

class DeleteOnt(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.command_str = "__"
        self.commands = [
            self.blank_command,
            "config\r\n",
            "no remote ont ont-{0}-{1}-{2}\r\n\r\n".format(
                self.port_indexes['slot_number'],
                self.port_indexes['port_number'],
                params.get('ont')
            ),
            self.blank_command,
            "no remote uniport uniport-{0}-{1}-{2}-2-1\r\n\r\n".format(
                self.port_indexes['slot_number'],
                self.port_indexes['port_number'],
                params.get('ont')
            ),
        ]
        self.success_message = "ONT {0}-{1}-{2} Deleted".format(
                self.port_indexes['slot_number'],
                self.port_indexes['port_number'],
                params.get('ont')
            )
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

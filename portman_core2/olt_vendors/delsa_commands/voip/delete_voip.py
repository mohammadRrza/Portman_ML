from ..base_command import BaseCommand


class DeleteVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = "__"

        self.commands = [
            "no ont sipconfig {0} port_id 1\r\n\r\n".format(
                params.get('ont')
            ),
            "no ont ipconfig {0} ip-index 1\r\n\r\n\r\n".format(
                params.get('ont')
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

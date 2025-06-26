from ..base_command import BaseCommand


class ShowVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = "display sippstnuser attribute {0} {1} {2}\r\n\r\n".format(
            self.port_indexes['port_number'],
            params.get('ont'),
            params.get('olt_ont_port_id')
        )
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.error_list = ["Failure: The user does not exist"]

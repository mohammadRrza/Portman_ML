from .base_command import BaseCommand


class PortOntInfoBySN(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = False
        self.command_str = "display ont info by-sn {0}\r\n\r\n".format(params.get('serial_number'))
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.error_list = ["The required ONT does not exist"]

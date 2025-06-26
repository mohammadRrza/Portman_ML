from .base_command import BaseCommand


class PortOntInfo(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = "display ont info {0} all\r\n\r\n".format(self.port_indexes['port_number'])
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'

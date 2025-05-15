from .base_command import BaseCommand


class ShowSnmpServerCommunity(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.clean_output_enabled = False
        self.command_str = "show snmp-server community\r\n\r\n"


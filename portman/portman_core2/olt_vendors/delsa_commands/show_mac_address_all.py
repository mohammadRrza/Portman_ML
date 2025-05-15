from .base_command import BaseCommand


class ShowMacAddressAll(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.command_str = "show mac-address all\r\n\r\n"


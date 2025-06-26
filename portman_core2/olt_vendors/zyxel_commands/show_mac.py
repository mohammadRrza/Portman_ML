from .base_command import BaseCommand


class ShowMac(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "show mac address-table all\r\n\r\n"


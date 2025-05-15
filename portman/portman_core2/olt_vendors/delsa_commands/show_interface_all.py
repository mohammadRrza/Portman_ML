from .base_command import BaseCommand


class ShowInterfaceAll(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.command_str = "show interface all\r\n\r\n"


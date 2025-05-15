from .base_command import BaseCommand


class ShowServicePortAll(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.command_str = "show service-port all\r\n\r\n"


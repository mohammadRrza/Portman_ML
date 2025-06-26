from .base_command import BaseCommand


class Backup(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = False
        self.command_str = "show configuration running\r\n\r\n"


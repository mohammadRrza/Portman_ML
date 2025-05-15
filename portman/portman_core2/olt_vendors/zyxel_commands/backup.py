from .base_command import BaseCommand


class Backup(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "show config-0\r\n\r\n n"


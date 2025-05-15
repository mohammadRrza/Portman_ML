from .base_command import BaseCommand


class Backup(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.clean_output_enabled = False
        self.command_str = "show running-config\r\n\r\n"


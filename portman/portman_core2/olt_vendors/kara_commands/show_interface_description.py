from .base_command import BaseCommand


class ShowInterfaceDescription(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = False
        self.command_str = 'show interface description'


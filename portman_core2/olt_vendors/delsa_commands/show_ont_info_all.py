from .base_command import BaseCommand


class ShowOntInfoAll(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.command_str = "show ont-info all\r\n\r\n"


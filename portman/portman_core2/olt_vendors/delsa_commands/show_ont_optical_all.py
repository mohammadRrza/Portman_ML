from .base_command import BaseCommand


class ShowOntOpticalAll(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.command_str = "show ont-optical all\r\n\r\n"


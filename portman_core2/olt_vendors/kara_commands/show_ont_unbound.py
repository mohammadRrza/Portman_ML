from .base_command import BaseCommand


class ShowOntUnbound(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = False
        self.command_str = "show ont-unbound\r\n\r\n"


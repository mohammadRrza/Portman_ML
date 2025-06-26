from .base_command import BaseCommand


class ShowOntInfo(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = False
        self.command_str = "show ont-info\r\n\r\n"
        self.garbage_list = ["Press any key to continue (Q to quit)", "                                      ", "\\r\\r"]


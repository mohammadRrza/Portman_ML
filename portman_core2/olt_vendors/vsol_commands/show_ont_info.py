from .base_command import BaseCommand


class ShowOntInfo(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.gpon_mode = True
        self.command_str = "show pon info\r\n\r\n"
        self.garbage_list = ["Press any key to continue (Q to quit)", "                                      ", "\\r\\r"]


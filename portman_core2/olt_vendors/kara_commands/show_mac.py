from .base_command import BaseCommand

class ShowMac(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "show mac-address-table"
        self.garbage_list = ["Press any key to continue (Q to quit)", "       Press any key to continue (Q to quit)", "                   "]
        

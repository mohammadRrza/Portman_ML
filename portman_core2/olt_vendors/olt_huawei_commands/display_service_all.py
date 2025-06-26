from .base_command import BaseCommand

class DisplayServiceAll(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "display service-port all\r\n\r\n" 

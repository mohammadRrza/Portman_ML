from .base_command import BaseCommand

class ShowMac(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "display mac-address all\r\n\r\n"
        self.regex_search_pattern = r'-{3,}|/\d+\s*/\d+|/\w+\s*/\w+'
        

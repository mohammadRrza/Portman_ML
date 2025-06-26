from .base_command import BaseCommand


class CardStatus(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "show lc status\r\n\r\n"
        

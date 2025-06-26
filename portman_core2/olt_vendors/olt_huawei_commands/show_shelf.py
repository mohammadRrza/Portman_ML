from .base_command import BaseCommand


class ShowShelf(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "display board 0\r\n\r\n"
        

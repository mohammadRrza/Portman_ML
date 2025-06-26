from .base_command import BaseCommand
import re


class ShowRemoteOnt(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "show remote ont\r\n\r\n"

    def send_result(self, status_code=200):
        result = BaseCommand.send_result(self, status_code)
        if result is None:
            return

        result['free_ont_id'] = self.findFirstFreeOntId();

        return result


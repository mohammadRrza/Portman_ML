from .base_command import BaseCommand
import re

class DisplayOntAutofind(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = False
        self.command_str = "display ont autofind all\r\n\r\n"
        self.error_list = ["The automatically found ONTs do not exist"]

    def send_result(self, status_code=200):
        result = BaseCommand.send_result(self, status_code)
        if result is None:
            return

        result['modems'] = self.extractModems(self.output, self.params.get('serial_number_ends_with', ''));

        return result




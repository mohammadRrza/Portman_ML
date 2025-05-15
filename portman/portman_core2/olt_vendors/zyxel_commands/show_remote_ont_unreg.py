from .base_command import BaseCommand
import re


class ShowRemoteOntUnreg(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "show remote ont unreg\r\n\r\n"

    def send_result(self, status_code=200):
        result = BaseCommand.send_result(self, status_code)
        if result is None:
            return

        result['modems'] = self.extractModems(self.output, self.params.get('serial_number_ends_with', ''));

        return result

    def extractModems(self, text, snEndsWith = ''):
        modems = []
        for match in re.finditer(r"\bUnReg\s+(\w+)\b", text):
            modems.append(match.group(1))

        filteredModems = modems
        if snEndsWith != '' :
            filteredModems = [modem for modem in modems if modem.endswith(snEndsWith.upper())]
            
        return filteredModems


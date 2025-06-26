from .base_command import BaseCommand
import re

class PortOntConfirm(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = 'ont confirm {0} sn-auth {1} omci ont-lineprofile-id {2} desc "{3}"\r\n\r\n'.format(
            self.port_indexes['port_number'],
            params.get('serial_number'),
            params.get('olt_profile_id'),
            params.get('desc')
        )
        self.error_list = ["Failure: The line profile does not exist"]

    def send_result(self, status_code=200):
        result = BaseCommand.send_result(self, status_code)
        if result is None:
            return

        result['ont_id'] = self.extractOntId(self.output);

        return result

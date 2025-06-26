from .base_command import BaseCommand

class DisplayServicePort(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "display service-port port 0/{0}/{1} ont {2}\r\n\r\n".format(
            self.port_indexes['slot_number'],
            self.port_indexes['port_number'],
            params.get('ont')
        )
        self.error_list = ["Failure: No service virtual port can be operated"]
        

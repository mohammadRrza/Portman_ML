from .base_command import BaseCommand

class UndoServicePortByPort(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "undo service-port port 0/{0}/{1} ont {2}\r\n\r\ny\r\n".format(
            self.port_indexes['slot_number'],
            self.port_indexes['port_number'],
            params.get('ont')
        )



from .base_command import BaseCommand

class UndoServicePort(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.command_str = "undo service-port {0}\r\n\r\n".format(
            params.get('service_port_index'),
        )



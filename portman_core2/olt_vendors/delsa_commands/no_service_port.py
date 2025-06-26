from .base_command import BaseCommand


class NoServicePort(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        self.command_str = "no service-port {0}\r\n\r\nsave\r\n".format(
            params.get('service_port_index'),
        )


from .base_command import BaseCommand

class SaveConfig(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = False
        self.command_str = "save data\r\n\r\n"
        self.error_list = ["System is busy, please save data later"]
        self.success_message = "System data has been saved completely."

    def fetch_command_output(self):
        # It will take several minutes to save configuration file, please wait...
        self.tn.write(bytes(self.command_str, 'utf-8')) ### main command
        result = self.tn.read_until(b"completely", 0.1)
        output = str(result)
        while 'completely' not in str(result):
            result = self.tn.read_until(b"completely", 0.1)
            output += str(result.decode('utf-8'))
        return self.set_command_output(output)

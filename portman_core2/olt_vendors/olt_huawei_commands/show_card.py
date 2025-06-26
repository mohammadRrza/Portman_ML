from .base_command import BaseCommand

class ShowCard(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = "display port state all\r\n\r\n"
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'

    def fetch_command_output(self):
        self.tn.write(bytes(self.command_str, 'utf-8')) ### main command
        result = self.tn.read_until(b"#", 0.1)
        for i in range(0, 150):
            self.tn.write(b'\r\n')
        output = self.tn.read_until(b"#", 4)
        return self.set_command_output(str(output))

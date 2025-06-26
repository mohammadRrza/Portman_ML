from ..base_command import BaseCommand


class ShowVoip(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.gpon_mode = True
        self.command_str = "show ont sipconfig {0} all\r\n\r\n".format(
            params.get('ont')
        )
        self.regex_sub_pattern = r"-.*37D"
        self.regex_search_pattern = r'-{4,}|\s{4,}|:'
        self.error_list = ["Failure: The user does not exist", "ONU is not exist"]

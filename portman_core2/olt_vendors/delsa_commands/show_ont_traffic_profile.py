from .base_command import BaseCommand


class ShowOntTrafficProfile(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.config_mode = True
        profileNameId = params.get('profile_id', "all")
        if (profileNameId.isnumeric()):
            self.command_str = "show ont-traffic-profile profile-id {0}\r\n\r\n".format(profileNameId)
        elif profileNameId.lower() == "all":
            self.command_str = "show ont-traffic-profile all\r\n\r\n"
        else:
            self.command_str = "show ont-traffic-profile profile-name {0}\r\n\r\n".format(profileNameId)

        self.error_list = ["Error, There's no trafficprofile exist"]


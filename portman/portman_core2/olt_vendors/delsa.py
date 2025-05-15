from .command_factory import CommandFactory
from .delsa_commands.show_interface_all import ShowInterfaceAll
from .delsa_commands.show_ont_info_all import ShowOntInfoAll
from .delsa_commands.show_service_port_all import ShowServicePortAll
from .delsa_commands.show_vlan_all import ShowVlanAll
from .delsa_commands.show_ont_traffic_profile import ShowOntTrafficProfile
from .delsa_commands.no_service_port import NoServicePort
from .delsa_commands.setup_ont import SetupOnt
from .delsa_commands.backup import Backup
from .delsa_commands.voip.add_voip import AddVoip
from .delsa_commands.voip.show_voip import ShowVoip
from .delsa_commands.voip.delete_voip import DeleteVoip
from .delsa_commands.show_ont_optical_all import ShowOntOpticalAll
from .delsa_commands.show_mac_address_all import ShowMacAddressAll
from .delsa_commands.find_sn_by_mac import FindSnByMac
from .delsa_commands.delete_ont import DeleteOnt
from .delsa_commands.reboot_ont import RebootOnt


class OltDelsa:
    command_factory = CommandFactory()
    command_factory.register_type('show interface all', ShowInterfaceAll)
    command_factory.register_type('show ont-info all', ShowOntInfoAll)
    command_factory.register_type('show ont-optical all', ShowOntOpticalAll)
    command_factory.register_type('show service-port all', ShowServicePortAll)
    command_factory.register_type('show mac-address all', ShowMacAddressAll)
    command_factory.register_type('show vlan all', ShowVlanAll)
    command_factory.register_type('show ont-traffic-profile', ShowOntTrafficProfile)
    command_factory.register_type('no service-port', NoServicePort)
    command_factory.register_type('get backup', Backup)
    command_factory.register_type('setup ont', SetupOnt)
    command_factory.register_type('delete ont', DeleteOnt)
    command_factory.register_type('reboot ont', RebootOnt)
    command_factory.register_type('add voip', AddVoip)
    command_factory.register_type('show voip', ShowVoip)
    command_factory.register_type('delete voip', DeleteVoip)
    command_factory.register_type('find sn by mac', FindSnByMac)


    @classmethod
    def execute_command(cls, oltInfo, command, params):
        command_class = cls.command_factory.make_command(oltInfo, command, params)
        return command_class.run_command()

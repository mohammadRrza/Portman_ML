from .command_factory import CommandFactory
from .kara_commands.show_interface_description import ShowInterfaceDescription
from .kara_commands.show_ont_info import ShowOntInfo
from .kara_commands.show_vlan import ShowVlan
from .kara_commands.show_mac import ShowMac
from .kara_commands.backup import Backup
from .kara_commands.show_ont_unbound import ShowOntUnbound


class OltKara:
    command_factory = CommandFactory()
    command_factory.register_type('show ont-unbound', ShowOntUnbound)
    command_factory.register_type('show ont-info', ShowOntInfo)
    command_factory.register_type('show vlan', ShowVlan)
    command_factory.register_type('show mac-address-table', ShowMac)
    command_factory.register_type('show mac', ShowMac)
    command_factory.register_type('get backup', Backup)
    command_factory.register_type('show interface description', ShowInterfaceDescription)


    @classmethod
    def execute_command(cls, oltInfo, command, params):
        command_class = cls.command_factory.make_command(oltInfo, command, params)
        return command_class.run_command()

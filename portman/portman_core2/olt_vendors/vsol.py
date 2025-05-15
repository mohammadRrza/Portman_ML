from .command_factory import CommandFactory
from .vsol_commands.show_interface_all import ShowInterfaceAll
from .vsol_commands.show_snmp_server_community import ShowSnmpServerCommunity
from .vsol_commands.show_ont_info import ShowOntInfo

class OltVsol:
    command_factory = CommandFactory()
    command_factory.register_type('show interface all', ShowInterfaceAll)
    command_factory.register_type('show snmp-server community', ShowSnmpServerCommunity)
    command_factory.register_type('show ont-info', ShowOntInfo)


    @classmethod
    def execute_command(cls, oltInfo, command, params):
        command_class = cls.command_factory.make_command(oltInfo, command, params)
        return command_class.run_command()

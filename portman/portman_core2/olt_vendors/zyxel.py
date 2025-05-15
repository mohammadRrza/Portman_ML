from .command_factory import CommandFactory
from .zyxel_commands.card_status import CardStatus
from .zyxel_commands.show_mac import ShowMac
from .zyxel_commands.show_remote_ont import ShowRemoteOnt
from .zyxel_commands.show_remote_ont_unreg import ShowRemoteOntUnreg
from .zyxel_commands.setup_ont import SetupOnt
from .zyxel_commands.delete_ont import DeleteOnt
from .zyxel_commands.backup import Backup


class OltZyxel:
    command_factory = CommandFactory()
    command_factory.register_type('card status', CardStatus)
    command_factory.register_type('show mac', ShowMac)
    command_factory.register_type('show remote ont', ShowRemoteOnt)
    command_factory.register_type('show remote ont unreg', ShowRemoteOntUnreg)
    command_factory.register_type('display ont autofind', ShowRemoteOntUnreg)
    command_factory.register_type('setup ont', SetupOnt)
    command_factory.register_type('delete ont', DeleteOnt)
    command_factory.register_type('get backup', Backup)


    @classmethod
    def execute_command(cls, oltInfo, command, params):
        command_class = cls.command_factory.make_command(oltInfo, command, params)
        return command_class.run_command()

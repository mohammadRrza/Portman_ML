from .command_factory import CommandFactory
from .olt_huawei_commands.show_mac import ShowMac
from .olt_huawei_commands.show_shelf import ShowShelf
from .olt_huawei_commands.show_card import ShowCard
from .olt_huawei_commands.port_ont_info import PortOntInfo
from .olt_huawei_commands.display_service_port import DisplayServicePort
from .olt_huawei_commands.display_service_all import DisplayServiceAll
from .olt_huawei_commands.display_ont_autofind import DisplayOntAutofind
from .olt_huawei_commands.port_ont_confirm import PortOntConfirm
from .olt_huawei_commands.port_ont_config import PortOntConfig
from .olt_huawei_commands.undo_service_port import UndoServicePort
from .olt_huawei_commands.undo_service_port_by_port import UndoServicePortByPort
from .olt_huawei_commands.delete_ont import DeleteOnt
from .olt_huawei_commands.show_ont import ShowOnt
from .olt_huawei_commands.voip.show_voip import ShowVoip
from .olt_huawei_commands.voip.delete_voip import DeleteVoip
from .olt_huawei_commands.voip.add_voip import AddVoip
from .olt_huawei_commands.MA5800x2.voip.add_voip import AddVoip as x2AddVoip
from .olt_huawei_commands.save_config import SaveConfig
from .olt_huawei_commands.port_ont_info_by_sn import PortOntInfoBySN
from .olt_huawei_commands.setup_ont import SetupOnt
from .olt_huawei_commands.backup import Backup
from .olt_huawei_commands.find_sn_by_mac import FindSnByMac

class OltHuawei:
    command_factory = CommandFactory()

    def initCommandFactory(self, oltInfo):
        self.command_factory.clear()
        self.command_factory.register_type('show mac', ShowMac)
        self.command_factory.register_type('show shelf', ShowShelf)
        self.command_factory.register_type('show card', ShowCard)
        self.command_factory.register_type('show port', PortOntInfo)
        self.command_factory.register_type('port ont info', PortOntInfo)
        self.command_factory.register_type('display service port', DisplayServicePort)
        self.command_factory.register_type('display service all', DisplayServiceAll)
        self.command_factory.register_type('display ont autofind', DisplayOntAutofind)
        self.command_factory.register_type('port ont confirm', PortOntConfirm)
        self.command_factory.register_type('service port config', PortOntConfig)
        self.command_factory.register_type('undo service port', UndoServicePort)
        self.command_factory.register_type('undo service port by port', UndoServicePortByPort)
        self.command_factory.register_type('delete ont', DeleteOnt)
        self.command_factory.register_type('show ont', ShowOnt)
        self.command_factory.register_type('save config', SaveConfig)
        self.command_factory.register_type('port ont info by sn', PortOntInfoBySN)
        self.command_factory.register_type('setup ont', SetupOnt)
        self.command_factory.register_type('get backup', Backup)
        self.command_factory.register_type('find sn by mac', FindSnByMac)

        self.command_factory.register_type('show voip', ShowVoip)
        self.command_factory.register_type('delete voip', DeleteVoip)
        if 'ma5800x2' in oltInfo['olt_type_name'].lower():
            self.command_factory.register_type('add voip', x2AddVoip)
        else:
            self.command_factory.register_type('add voip', AddVoip)

    @classmethod
    def execute_command(cls, oltInfo, command, params):
        cls.initCommandFactory(cls, oltInfo=oltInfo)
        command_class = cls.command_factory.make_command(oltInfo, command, params)
        return command_class.run_command()

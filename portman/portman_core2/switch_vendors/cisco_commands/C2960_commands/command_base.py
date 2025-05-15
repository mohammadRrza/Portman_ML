import abc


class BaseCommand(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run_command(self):
        raise NotImplementedError()

    def showInterface(self, sshClient, description):
        showIntCommand = "sho int des | i {0}".format(description)
        return sshClient.send_command(showIntCommand)

    def findInterfaceByDescription(self, commandOutput, description):
        lines = commandOutput.split('\n')
        for line in lines:
            if description in line:
                parts = line.split()
                interface = parts[0]
                status = parts[1]
                status = parts[2] if status == 'admin' else status
                return True, interface, status
        return False, None, None

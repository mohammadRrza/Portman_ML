import jsonrpclib

from socket import error as SocketError
import threading

_local_user = threading.local()


def set_current_user(user):
    _local_user.user = user


def get_current_user():
    return getattr(_local_user, 'user', None)


def shutdown_portman(self):
    c = jsonrpclib.Server('http://localhost:7060')
    try:
        c.shutdown_portman()
    except SocketError as ex:
        return 'PortmanCore is shutdown'
    except Exception as ex:
        return 'give error when shuttdown PortmanCore'


def olt_run_command(olt_id, command, params):
    c = jsonrpclib.Server('http://localhost:7060')
    return c.olt_add_command(olt_id, command, params)

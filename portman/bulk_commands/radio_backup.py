from Commands.get_mikrotik_radio_backup import GetMikrotikRadiobackUp
from Commands.get_backups import GetbackUp

if __name__ == '__main__':
    radio_backup = GetMikrotikRadiobackUp()
    radio_backup.run_command()

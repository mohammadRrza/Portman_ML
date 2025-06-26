import sys
import os

PORTMAN_ENV = os.environ.get('PORTMAN_ENV', 'prod')
if PORTMAN_ENV == 'prod':
    sys.path.append('/opt/portmanv3/portman_web/')
elif PORTMAN_ENV == 'stage':
    sys.path.append('/opt/projects/portmanv3/portman_web/')
else:
    username = os.environ.get('USER', os.environ.get('USERNAME'))
    sys.path.insert(0, '/home/'+username+'/projects/portmanv3/portman_web/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from dslam.models import DSLAM
from dslam.models import DSLAMPort
from dslam.models import DSLAMPortSnapshot
from dslam.models import LineProfile
from dslam.models import DSLAMEvent
from dslam.models import DSLAMPortEvent
from dslam.models import DSLAMPortEvent
from dslam.models import Command
from dslam.models import PortCommand
from dslam.models import DSLAMCommand
from dslam.models import TelecomCenter
from dslam.models import DSLAMType
from dslam.models import City
from dslam.models import DSLAMBulkCommandResult
from dslam.models import DSLAMPortVlan
from dslam.models import Vlan
from dslam.models import DSLAMPortMac
from dslam.models import DSLAMBoard
from dslam.models import LineProfileExtraSettings
from dslam.models import DSLAMTypeCommand
from dslam import utility
from config.settings import SWITCH_BACKUP_PATH, MIKROTIK_ROUTER_BACKUP_PATH, CISCO_ROUTER_BACKUP_PATH, OLT_BACKUP_PATH
from config.settings import MIKROTIK_RADIO_BACKUP_PATH, VOIP_BACKUP_PATH, VLAN_BRIEF_PATH, DSLAM_BACKUP_PATH
from olt import utility as olt_utility
from olt.models import OLT, FAT
from cartable.models import Reminder
from cloud.models import ConfigRequest
from classes.mailer import Mail

from django.contrib.auth.models import Group as AuthGroup, Permission as AuthPermission
from users.models import User


#RouterModels
from router.models import Router


#SwitchModels
from switch.models import Switch

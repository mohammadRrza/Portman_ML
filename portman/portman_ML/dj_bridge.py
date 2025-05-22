import sys
import os

sys.path.append(r"C:\Users\m.taherabadi\Desktop\portmanv3-stage\portman\portman_web")
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from dslam.models import DSLAMPort

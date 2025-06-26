from datetime import datetime
from contact.models import DataLocationsLog


class LocationsActionsLogging:
    def __init__(self, params):
        self.log_date = datetime.now()
        self.log_parameter = params
        self.save_to_db()

    def save_to_db(self):
        DataLocationsLog.objects.create(username=self.log_parameter.get('username'),
                                        new_ip=self.log_parameter.get('new_ip'),
                                        action=self.log_parameter.get('action'),
                                        old_ip=self.log_parameter.get('old_ip'),
                                        result=self.log_parameter.get('result'),
                                        log_date=self.log_date,
                                        status=self.log_parameter.get('status'))

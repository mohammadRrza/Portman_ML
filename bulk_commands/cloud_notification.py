from datetime import datetime, date
from dj_bridge import ConfigRequest, Reminder, User


def get_expiring_config_request():
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    return ConfigRequest.objects.filter(due_date__isnull=False, due_date__lte=today_end, #, due_date__gte=today_start
                                        is_reminded=False).distinct('device__ip')


def create_remindr():
    config_requests = get_expiring_config_request()

    if config_requests:
        ips = config_requests.values_list('device__ip', flat=True)
        title = 'سرویس‌های پهنای باند در حال انقضا'
        sending_methods = 'Email,In_App'
        separator = '\r\n'
        description = (f"همکار گرامی سرویس های زیر در حال انقاضا میباشند:\r\n"
                       f"{separator.join(ips)}\r\n"
                       f"لطفا اقدامات لازم را مبذول فرمایید."
                       )
        users = User.objects.filter(groups__name='CLOUD_ADMIN')

        for user in users:
            Reminder.objects.create(title=title, description=description, user=user,
                                    sending_methods=sending_methods, reminder_time=datetime.now())

        config_requests.update(is_reminded=True)


if __name__ == '__main__':
    create_remindr()
    #print('run')

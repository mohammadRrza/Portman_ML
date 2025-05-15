import datetime
import os
import sys
from .ticket_service import Ticket
from dj_bridge import MIKROTIK_ROUTER_BACKUP_PATH


def get_backup_error_file():
    try:
        if os.path.exists(MIKROTIK_ROUTER_BACKUP_PATH + 'router_backup_errors.txt'):
            os.remove(MIKROTIK_ROUTER_BACKUP_PATH + 'router_backup_errors.txt')
        filenames = []
        backup_errors_file = open(MIKROTIK_ROUTER_BACKUP_PATH + 'router_backup_errors.txt', 'w')
        for filename in os.listdir(MIKROTIK_ROUTER_BACKUP_PATH):
            if filename.__contains__('Error') and filename.__contains__(
                    str(datetime.datetime.now().date() - datetime.timedelta(2))):
                f = open(MIKROTIK_ROUTER_BACKUP_PATH + filename, "r")
                err_text = filename + "   " + "|" + "   " + f.read()
                backup_errors_file.write(err_text + '\n\n')
                filenames.append(err_text)
                f.close()
            else:
                continue
        backup_errors_file.close()
        return backup_errors_file
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print({'row': str(ex) + "  // " + str(exc_tb.tb_lineno)})


def create_ticket():
    backup_errors_file = get_backup_error_file()
    file_path = os.path.abspath(backup_errors_file.name)
    file_size = os.path.getsize(file_path)
    if file_size > 0:
        title = f"وجود مشکل در بکاپ گرفتن برخی از روترها"
        message = f"با عرض سلام و احترام" \
                  f"<br />" \
                  f"سرور پورتمن با آی پی 172.28.246.130 قادر به گرفتن بکاپ از برخی روترها نبوده است که گزارش آن در فایل پیوست قرار دارد." \
                  f"<br />" \
                  f"لذا لطفا موارد را بررسی نمایید و در صورت وجود مشکل آن را برطرف نمایید." \
                  f"<br />" \
                  f"با تشکر"
        staff_group_id = "23d5e34c-789c-4d54-a68a-87bdf482d9fb"
        ticket = Ticket(message, title, staff_group_id)
        ticket_result = ticket.send_new_ticket()
        ticket_id = ticket_result.get('ResultId')
        ticket.attach_file(ticket_id, file_path)



import subprocess
import os
from pathlib import Path
from dj_bridge import Router, Switch
from .ticket_service import Ticket


def is_accessible(ip):
    result = subprocess.call(['ping', '-c', '1', '-W', '3', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result == 0


def send_ticket(title, message, staff_group_id, file_path):
    ticket = Ticket(message, title, staff_group_id)
    ticket_result = ticket.send_new_ticket()
    ticket_id = ticket_result.get('ResultId')
    ticket.attach_file(ticket_id, file_path)


def write_ping_results(devices, output_file):
    output_folder = Path(__file__).resolve().parent.parent / "files"
    os.makedirs(output_folder, exist_ok=True)
    output_path = output_folder / output_file

    with open(output_path, "w") as file:
        for device in devices:
            ip = device.device_ip
            if not is_accessible(ip):
                file.write(f"{ip} is inaccessible.\n")

    file_size = os.path.getsize(output_path)
    if file_size > 0:

        if 'routers' in output_file:
            device_name = 'روترها'
            staff_group_id = "23d5e34c-789c-4d54-a68a-87bdf482d9fb"

        else:
            device_name = 'سوئیچ ها'
            staff_group_id = "6ea5b9ba-29f0-4642-b093-b140b57b7806"

        title = f"عدم دسترسی پورتمن به برخی از {device_name}"
        message = f"با عرض سلام و احترام" \
                  f"<br />" \
                  f"سرور پورتمن با آی پی 172.28.246.130 به برخی از {device_name} دسترسی ندارد که مجموعه آنها در داخل فایل پیوست قرار دارد." \
                  f"<br />" \
                  f"لذا لطفا موارد را بررسی نمایید و در صورت وجود مشکل آن را برطرف نمایید." \
                  f"<br />" \
                  f"با تشکر"

        send_ticket(title, message, staff_group_id, output_path)


def check_routers_ping():
    routers = Router.objects.all()
    output_file = "routers_ping_result.txt"
    write_ping_results(routers, output_file)


def check_switch_ping():
    switches = Switch.objects.all()
    output_file = "switches_ping_result.txt"
    write_ping_results(switches, output_file)


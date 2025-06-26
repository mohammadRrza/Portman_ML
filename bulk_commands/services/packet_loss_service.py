import datetime
import os
from dj_bridge import DSLAM
import utility
from services.ticket_service import Ticket


class PacketLoss:

    def get_dslams(self):
        excluded_ips = ['172.19.159.186', '172.18.83.18', '172.18.83.22', '172.18.83.6', '172.18.83.2', '172.18.83.14',
                        '172.18.83.26', '172.18.83.10']
        dslam_list = DSLAM.objects.all().exclude(name__icontains='collected').exclude(ip__in=excluded_ips)
        return dslam_list

    def send_ticket(self, file_path):
        title = 'Dslam With Packet Loss'
        message = 'با عرض سلام و احترام لطفا مشکل موارد داخل فایل پیوست را بررسی نمایید.'
        staff_group_id = "23d5e34c-789c-4d54-a68a-87bdf482d9fb"
        ticket = Ticket(message, title, staff_group_id)
        ticket_result = ticket.send_new_ticket()
        ticket_id = ticket_result.get('ResultId')
        ticket.attach_file(ticket_id, file_path)

    def check_packet(self):
        dslam_list = self.get_dslams()
        params = dict(coutn=4, timeout=0.2)
        current_directory = os.getcwd()
        file_name = 'dslam_with_packet_loss.txt'
        file_path = os.path.join(current_directory, file_name)
        with open(file_name, 'w') as file:
            for item in dslam_list:
                try:
                    result = utility.run_icmp_command(item.id, 'ping', params)
                    if int(result.get('packet_loss')) == 100:
                        print(result)
                        date = datetime.datetime.now().strftime("%Y/%m/%d  %H:%M:%S")
                        information = f"ip: {item.ip}\nfqdn: {item.fqdn}\npacket_loss: {result.get('packet_loss')}\ndate: {date}\n"
                        information += "____________________________________________________\n"
                        file.write(information)
                except Exception as e:
                    print(e)
                    continue
        file_size = os.path.getsize(file_path)
        if file_size > 0:
            self.send_ticket(file_path)

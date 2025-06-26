#from django.test import TestCase
from unittest import TestCase
import re, math
from classes.mailer import Mail


class ConfigRequestTestCase(TestCase):
    def setUp(self):
        pass

    def test_check_run_was_successfull(self):
        command_output = 'sw-3750-cloud-rack25#conf t Enter configuration commands, one per line. End with CNTL/Z. sw-3750-cloud-rack25(config)#policy-map DEDICATED-LIMIT sw-3750-cloud-rack25(config-pmap)#class USER-185.126.2.180 sw-3750-cloud-rack25(config-pmap-c)#police \
        208666624 1000000 exceed-action drop 15200 1000000 exceed-action drop sw-3750-cloud-rack25(config-pmap-c)#^Z sw-3750-cloud-rack25# Check Result: sw-3750-cloud-rack25#sho run | s class USER-185.126.2.180 class USER-185.126.2.180 police \
        208664000 1000000 exceed-action drop sw-3750-cloud-rack25#'
        print(self.checkWasSuccessfull(command_output=command_output, checkClose=True, bandwidth=199))

    def test_can_send_email(self):
        mail_info = Mail()
        mail_info.from_addr = 'oss-notification@pishgaman.net'
        mail_info.to_addr = ', '.join(['M.Pourgharib@pishgaman.net' ,'f.azad@pishgaman.net'])
        mail_info.msg_body = "----\r\nIP: USER-{0}\r\nNew Bandwith: {1}\r\nStatus: {2}\r\n\r\nCommand Logs:\r\n{3}".format(
            "10.2.32.255",
            122,
            "DONE",
            'alongtext--------------along text'
        )
        mail_info.msg_subject = 'Cloud Services - Config Ran'
        Mail.Send_Mail(mail_info)


    def checkWasSuccessfull(self, command_output, checkClose = True, bandwidth=200):
        if 'police' not in command_output:
            return [False, 0]

        parts = re.findall("(.*) police (.*) (.*) exceed", command_output)
        if (parts[0] is None or parts[0][1] is None):
            return [False, 0]
        currentBW = parts[0][1]

        isClose = True
        if checkClose:
            print(int(bandwidth * 1024 * 1024 / 10000), int(int(currentBW) / 10000))
            isClose = math.isclose(int(bandwidth * 1024 * 1024 / 10000), int(int(currentBW) / 10000))

        return [
            isClose,
            int(int(currentBW) / 1024 / 1024) + 1
        ]
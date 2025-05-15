from .base_command import BaseCommand
import time
import re

class FindSnByMac(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.output = ''
        self.command_str = "__"
        self.regex_search_pattern = r'-{3,}|/\d+\s*/\d+|/\w+\s*/\w+'
        self.error_list = [
            "The automatically found ONTs do not exist", 
            "Failure: The line profile does not exist",
            "Failure: The traffic table does not exist"
        ]

    def send_result(self, status_code=200):
        return dict(result=self.output, status=status_code)

    def fetch_command_output(self):
        end_str = self.get_end_str() 
        
        def exe_command(command, sleepTime = 0):
            #print("command", command)
            self.tn.write(bytes(command + "\r\n\r\n", 'utf-8'))
            if sleepTime > 0:
                time.sleep(sleepTime)
            result = self.tn.read_until(bytes(end_str, 'utf-8'), 10)
            self.output += str(result.decode('utf-8'))
            return str(result.decode('utf-8'))

        if self.params['mac_address'] == '' or self.params['mac_address'] == None:
            self.output = "Failure: Mac Address is wrong"
            return

        def find_port_by_mac(text, macAddress):
            board = None
            slot = None
            port = None
            ontID = None

            for line in text.split('\r\n'):
                if (macAddress + " ") in line:
                    parts = line.split()
                    ontID = parts[8] if len(parts) > 3 else None
                    ontID = ''.join(re.findall(r'\d+', ontID))
                    port = parts[7] if len(parts) > 3 else None
                    port = ''.join(re.findall(r'\d+', port))
                    slot = parts[6] if len(parts) > 3 else None
                    slot = ''.join(re.findall(r'\d+', slot))
                    board = parts[5] if len(parts) > 3 else None
                    board = ''.join(re.findall(r'\d+', board))

            return board, slot, port, ontID


        # Finding Modem
        exe_command("display mac-address all | include {0}".format(self.params['mac_address']))
        board, slot, port, ontID = find_port_by_mac(self.output, self.params['mac_address'])
        if port == None or slot == None:
            self.output = "Failure: Slot & Port not found by serial number {0}".format(self.params['mac_address'])
            return

        # change interface
        selectingInterfaceCommand = "interface gpon {0}/{1}\r\n\r\n".format(int(board), int(slot))
        self.gpon_mode = True
        end_str = "(config-if-gpon-{0}/{1})#".format(int(board), int(slot)) #self.get_end_str()
        exe_command(selectingInterfaceCommand)

        self.output = ""
        ontInfoCommand = "display ont info {0} {1}\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n".format(int(port), int(ontID))
        #exe_command(ontInfoCommand)

        self.tn.write(bytes(ontInfoCommand + "\r\n\r\n", 'utf-8'))
        time.sleep(1) # important sleep here
        while True:
            chunk = self.tn.read_very_eager().decode('utf-8')
            self.output += chunk
            if "--More--" in chunk:
                self.tn.write(b"\n")
            else:
                break

        def find_key_in_output(keyword, text):
            value = None
            for line in text.split('\r\n'):
                if (keyword + "  ") in line:
                    parts = line.split(":")
                    value = parts[1].strip() if len(parts) > 1 else None
            return value

        exe_command("exit\r\nexit\r\nexit\r\n")

        sn =  find_key_in_output("SN", self.output)

        self.output = "Serial Number: {0}".format(sn) if sn != None else self.output

        return self.send_result()
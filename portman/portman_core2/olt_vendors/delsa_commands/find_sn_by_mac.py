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
            port = None
            ont = None

            for line in text.split('\r\n'):
                if (macAddress + "  ") in line:
                    parts = line.split()
                    port = parts[3] if len(parts) > 3 else None
                    port = ''.join(re.findall(r'\d+', port))
                    ont = parts[4] if len(parts) > 3 else None
                    ont = ''.join(re.findall(r'\d+', ont))

            return port, ont


        # Finding Modem
        exe_command("show mac-address mac {0}".format(self.params['mac_address']))
        port, ontID = find_port_by_mac(self.output, self.params['mac_address'])
        if port == None or ontID == None:
            self.output = "Failure: Port not found by serial number {0}".format(self.params['mac_address'])
            return

        # change interface
        selectingInterfaceCommand = "interface gpon {0}\r\n\r\n".format(int(port))
        self.gpon_mode = True
        end_str = "(config-gpon-{0})#".format(int(port)) #self.get_end_str()
        exe_command(selectingInterfaceCommand)

        self.output = ""
        ontInfoCommand = "show ont-info {0}\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n".format(int(ontID))
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

        sn =  find_key_in_output("SerialNumber", self.output)

        self.output = "Serial Number: {0}".format(sn) if sn != None else self.output

        return self.send_result()
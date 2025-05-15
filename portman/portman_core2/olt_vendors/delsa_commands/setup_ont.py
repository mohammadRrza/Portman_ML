from .base_command import BaseCommand
import time

class SetupOnt(BaseCommand):
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
            result = self.tn.read_until(bytes(end_str, 'utf-8'), 4)
            self.output += str(result.decode('utf-8'))
            return str(result.decode('utf-8'))

        if self.params['serial_number'] == '' or self.params['serial_number'] == None:
            self.output = "Failure: Serial number is wrong"
            return

        # Finding Modem
        exe_command("show ont-info all")
        modems = self.extractModems(self.output, self.params['serial_number'])
        if len(modems) == 0:
            self.output = "Failure: Modem not found by serial number {0}".format(self.params['serial_number'])
            return

        selectedOnt = modems[0]
        selectedSerial = selectedOnt['serial']
        selectedPortID = selectedOnt['slot_port'][0]
        selectedOntID = selectedOnt['slot_port'][1]
        selectedEquipmentId = selectedOnt['equipment_id']

        if str(selectedOntID).isnumeric() == False:
            self.output = "Failure: Modem is not connected {0}".format(self.params['serial_number'])
            return

        # Port Ont Config
        portOntConfigCommand = "service-port vlan {0} gpon {1} ont {2} gemport {3} multi-service user-vlan {4} tag-transform translate traffic-outbound {5}\r\n\r\n".format(
            self.params.get('olt_vlan_number'),
            selectedPortID,
            selectedOntID,
            self.params.get('olt_gemport'),
            self.params.get('olt_vlan_number'),
            self.params.get('olt_outbound_index'),
        )

        self.output = ""
        exe_command(portOntConfigCommand)
        self.output = dict(
            slot=selectedPortID if selectedPortID else self.port_indexes['slot_number'], 
            port=selectedOntID if selectedOntID != None else self.port_indexes['port_number'], 
            serial=selectedSerial, 
            ont_id=selectedOntID,
            equipment_type=selectedEquipmentId
        )

        return self.send_result()
        



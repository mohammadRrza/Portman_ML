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
            print(command, "######")
            self.tn.write(bytes(command + "\r\n\r\n", 'utf-8'))
            if sleepTime > 0:
                time.sleep(sleepTime)
            result = self.tn.read_until(bytes(end_str, 'utf-8'), 4)
            self.output += str(result)
            return str(result)

        if self.params['serial_number'] == '' or self.params['serial_number'] == None:
            return self.send_result(500)

        # Finding Modem
        exe_command("display ont autofind all")
        modems = self.extractModems(self.output, self.params['serial_number'])
        print(modems, "*******####")
        if len(modems) == 0:
            return self.send_result(500)

        selectedOnt = modems[0]
        selectedSerial = selectedOnt['serial']
        selectedSlot = selectedOnt['slot_port'][1]
        selectedPort = selectedOnt['slot_port'][2]
        selectedEquipmentId = selectedOnt['equipment_id']
        
        # Going to GPON mode
        end_str = '(config-if-gpon'
        exe_command(self.get_gpon_command(selectedSlot))

        # Port Ont Confirm & Exit from GPON mode
        end_str = self.get_end_str()
        portOntConfirmCommand = 'ont confirm {0} sn-auth {1} omci ont-lineprofile-id {2} desc "{3}"\r\n\r\nquit'.format(
            selectedPort,
            selectedSerial,
            self.params.get('olt_profile_id'),
            self.params.get('description')
        )
        exe_command(portOntConfirmCommand)
        ontId = self.extractOntId(self.output)
        if str(ontId).isnumeric() == False:
            return self.send_result(500)

        # Port Ont Config
        portOntConfigCommand = "service-port vlan {0} gpon 0/{1}/{2} ont {3} gemport {4} multi-service user-vlan {5} tag-transform translate inbound traffic-table index {6} outbound traffic-table index {7}\r\n\r\n".format(
            self.params.get('olt_vlan_number'),
            selectedSlot,
            selectedPort,
            ontId,
            self.params.get('olt_gemport'),
            self.params.get('olt_vlan_number'),
            self.params.get('olt_inbound_index'),
            self.params.get('olt_outbound_index'),
        )

        exe_command(portOntConfigCommand)

        self.output = dict(
            slot=selectedSlot, 
            port=selectedPort, 
            serial=selectedSerial, 
            ont_id=ontId,
            equipment_type=selectedEquipmentId
        )

        return self.send_result()
        



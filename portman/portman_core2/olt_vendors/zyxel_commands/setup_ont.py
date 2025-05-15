from .base_command import BaseCommand


class SetupOnt(BaseCommand):
    def __init__(self, params):
        BaseCommand.__init__(self, params)
        self.output = ''
        self.command_str = "__"
        self.error_list = ['Error: ONT serial number should be unique in a PON port']

    def fetch_command_output(self):
        end_str = self.get_end_str() 
        
        def exe_command(command):
            print(command, "######")
            self.tn.write(bytes(command + "\r\n\r\n", 'utf-8'))
            result = self.tn.read_until(bytes(end_str, 'utf-8'), 2)
            self.output += str(result)

        if self.params['serial_number'] == '' or self.params['serial_number'] == None:
            self.output = "Serial number is missed"
            return self.send_result(422)
        
        exe_command(self.blank_command)

        exe_command("show remote ont")
        freeOntId = self.findFirstFreeOntId()
        if str(freeOntId).isnumeric() == False:
            return self.send_result(500)

        exe_command(self.blank_command)
        end_str = "(config)#"
        exe_command("config")
        end_str = "(config-ont)#"
        exe_command("remote ont ont-{0}-{1}-{2}".format(
                self.port_indexes['slot_number'],
                self.port_indexes['port_number'],
                freeOntId
            ))
        exe_command("inactive")
        exe_command("SN {0}".format(self.params['serial_number']))
        exe_command("Description {0}".format(self.params['description']))
        exe_command("bwgroup 1 usbwprofname 1G dsbwprofname 1G")
        exe_command("no inactive")
        end_str = "(config)#"
        exe_command("exit")
        end_str = "-uniport)#"
        exe_command("remote uniport uniport-{0}-{1}-{2}-2-1".format(
                self.port_indexes['slot_number'],
                self.port_indexes['port_number'],
                freeOntId
            ))
        exe_command("inactive")
        exe_command("queue tc 0 bwgroup 1")
        exe_command("vlan {0} network {1} ingprof alltc".format(self.params['olt_vlan_number'], self.params['olt_vlan_number']))
        exe_command("pvid {0}".format(self.params['olt_vlan_number']))
        exe_command("no inactive")
        end_str = "(config)#"
        exe_command("exit")

        self.output = dict(
            slot=self.port_indexes['slot_number'], 
            port=self.port_indexes['port_number'], 
            serial=self.params['serial_number'], 
            ont_id=freeOntId,
            equipment_type=""
        )

        return self.send_result()


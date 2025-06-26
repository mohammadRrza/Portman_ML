import os
import sys
import telnetlib
import time
import re
from socket import error as socket_error

class BaseCommand:
    def __init__(self, params):
        self.params = params
        self.__HOST = None
        self.__telnet_username = None
        self.__telnet_password = None
        self.retry = 1
        self.max_try = 4
        self.simulate = False
        self.command_str = None
        self.output = None
        self.gpon_mode = False
        self.request_from_ui = params.get('request_from_ui')
        self.port_indexes = params.get('port_conditions')
        self.regex_search_pattern = r'-{3,}|\s{3,}'
        self.regex_sub_pattern = r"-+\s[a-zA-Z\s(\')-]+\S+\s+\S\[37D"
        self.clean_output_enabled = True
        self.error_list = None
        self.success_message = None

    @property
    def HOST(self):
        return self.__HOST

    @HOST.setter
    def HOST(self, value):
        self.__HOST = value

    @property
    def telnet_username(self):
        return self.__telnet_username

    @telnet_username.setter
    def telnet_username(self, value):
        self.__telnet_username = value

    @property
    def telnet_password(self):
        return self.__telnet_password

    @telnet_password.setter
    def telnet_password(self, value):
        self.__telnet_password = value

    # Establishes a telnet connection to device
    def telnet(self):
        self.tn = telnetlib.Telnet(self.__HOST)
        return self.tn

    # Login to device
    def login(self):
        tn = self.telnet()
        if tn.read_until(b'username:'):
            tn.write((self.__telnet_username + "\r\n").encode('utf-8'))
        if tn.read_until(b'password:'):
            tn.write((self.__telnet_password + "\r\n").encode('utf-8'))

        tn.write(b"end")
        err = tn.read_until(b'end', 3)
        if 'invalid' in str(err):
            return dict(result='Telnet Username or Password is wrong! Please contact with core-access department.',
                        status=500)
        if 'Reenter times' in str(err):
            return dict(result='The device is busy right now. Please try a few moments later.',
                        status=500)
        tn.write(b"\r\n")
        return True

    # Logout from device
    def logout(self):
        if self.gpon_mode is True:
            self.tn.write(b"quit\r\n")

        self.tn.write(b"quit\r\n")
        self.tn.write(b"quit\r\n")
        self.tn.write(b"y\r\n")
        self.tn.close()

    # Going to config mode of device
    def enable_config_mode(self):
        self.tn.write(b"\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n")
        self.tn.write(b"enable\r\n")
        self.tn.write(b"config\r\n")
        self.tn.read_until(b"(config)#", 3)
        return True

    def get_gpon_command(self, slotNumber = None):
        if slotNumber != None:
            slot_number = slotNumber
        else:
            slot_number = self.port_indexes['slot_number']
        if len(slot_number) == 0 or slot_number == "" or slot_number == " ":
            slot_number = "1"
        
        return "interface gpon {0}".format(slot_number)

    # Going to gpon mode
    def enable_gpon_mode(self):
        if self.gpon_mode is False:
            return True

        #time.sleep(1)
        self.tn.write(bytes(self.get_gpon_command() + "\r\n", 'utf-8'))
        result = self.tn.read_until(b"#", 1)
        print("::: Gpon Mode Result :::", str(result))

        if 'Failure' in str(result):
            return dict(result='Gpon Failure: This board does not exist.', status=500)
        if "Unknown command" in str(result):
            return dict(result="Ont pon number is wrong.", status=500)
        time.sleep(1)
        return True

    def set_command_output(self, value):
        self.output = value
        print("::: Main Command Result :::", self.output)
        return self.output

    # Find end of result by this string
    def get_end_str(self):
        end_str = "(config)#"
        if self.gpon_mode is True:
            end_str = '(config-gpon-'
        return end_str

    # Main function which run our main command
    def fetch_command_output(self):
        end_str = self.get_end_str()
        self.tn.write(bytes(self.command_str, 'utf-8')) ### main command
        result = self.tn.read_until(bytes(end_str, 'utf-8'), 1)
        output = str(result)
        while (end_str not in output):
            self.tn.write(b"\r\n")
            result = self.tn.read_until(bytes(end_str, 'utf-8'), 0.1)
            output += str(result.decode('utf-8'))
            
        return self.set_command_output(output)

    # Executes the command and returns the native output
    def execute_command(self):
        if self.command_str is None:
            return

        return self.fetch_command_output()

    # If there is any error, we can try again a couple of times
    def try_again(self, e):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(fname + " > " + str(exc_tb.tb_lineno))
        print(e)
        self.retry += 1
        if self.retry < self.max_try:
            return self.run_command()

    # Cleaning output from extra unnecessary inforamtions
    def clean_output(self, result):
        if self.clean_output_enabled is False:
            return result

        result = [re.sub(self.regex_sub_pattern, "", val) for val in result if
                    re.search(self.regex_search_pattern, val)]

        return result

    # Prepares and returns the result of command to the client
    def send_result(self, status_code=200):
        if self.output is None:
            return

        if (status_code == 200 and self.success_message is not None):
            return dict(result=self.success_message, status=status_code)

        result = self.output.split("\\r\\n")
        result = self.clean_output(result)

        if self.request_from_ui:
            return dict(result="\r\n".join(result), status=status_code)
            
        return dict(result=result, status=status_code)

    # Finds known errors
    def fetch_output_errors(self):
        if self.output is None:
            return False

        if self.error_list is not None:
            for error_txt in self.error_list:
                if error_txt in self.output:
                    return dict(result=error_txt + " ({0})".format(self.command_str), status=500)

        if 'Failure: This board does not exist' in self.output:
            return dict(result="Failure: This board does not exist. ({0})".format(self.command_str), status=500)

        if 'Unknown command,' in self.output:
            return dict(result='Unknown command: ' + self.command_str, status=500)

        if 'Parameter error,' in self.output:
            return dict(result="Parameter error, check inputs and try again. ({0}) - ({1})".format(self.command_str, self.output), status=500)

        if 'Failure: ' in self.output:
            self.clean_output_enabled = False
            return self.send_result(500)

        return False

    # The whole procces of running a command in device
    def run_command(self):
        
        if self.simulate is True:
            self.output = self.command_str
            return self.send_result()

        try :   
            logged_in = self.login()
            if (logged_in is not True):
                return logged_in
            
            self.enable_config_mode()
            
            gpon_mode_enabled = self.enable_gpon_mode()
            if gpon_mode_enabled is not True:
                self.logout()
                return gpon_mode_enabled

            self.execute_command()
            self.logout()

            has_error = self.fetch_output_errors()
            if has_error is not False:
                return has_error

            return self.send_result()
        except (EOFError, socket_error) as e:
            self.try_again(e)
        except Exception as e:
            self.try_again(e)


    ################################ SHARED FUNCTIONS
    def extractOntId(self, string):
        match = re.search(r'ONTID\s*:\s*(\d+)', string)
        if match:
            ont_id = match.group(1)
            return ont_id
        return None

    def extractModems(self, text, snEndsWith = ''):
        # Extract PON/ONU numbers
        modems = []

        for line in text.split('\r\n'):
            match = re.search(r"^(?:\d+\/\d+\s+.*)$", line)
            if match:
                main = match.group()
                parts = re.search(r"^(\d+\/\d+)\s+(\w+).*$", main)
                if snEndsWith.lower() in parts[2].lower():
                    modems.append(dict(slot_port=parts[1].split('/'), serial=parts[2], equipment_id="unknown"))

        return modems
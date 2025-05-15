from dslam.models import DSLAM
from dslam import utility
from rest_framework import status
import re
from datetime import datetime


class GetPortStatusParamsService:
    def __init__(self, data, device_ip):
        self.data = data
        self.device_ip = device_ip

    def get_port_params(self):
        print('============================================================================')
        print(self.device_ip)
        print(self.data)
        print('============================================================================')
        dslam_id = self.data.get('dslam_id')
        dslamObj = DSLAM.objects.get(pk=dslam_id)
        params = self.data.get('params', None)
        dslam_type = dslamObj.dslam_type_id

        try:
            if dslam_type == 3:
                result = utility.dslam_port_run_command(dslam_id, 'show linerate', params)

                if result.get('status') == 200:
                    result = str(result['result']).split("\r\n")
                    result = [re.sub(r'\s+--P[a-zA-Z +\\1-9[;-]+H', '', val) for val in result if
                              re.search(r'\s{3,}', val)]

                    port_status = {
                        'ADSL_DOWNSTREAM_SNR': "",
                        'ADSL_UPSTREAM_SNR': "",
                        'ADSL_CURR_DOWNSTREAM_RATE': "",
                        'ADSL_CURR_UPSTREAM_RATE': ""
                    }
                    for inx, val in enumerate(result):
                        if "DownStream Margin" in val:
                            ADSL_UPSTREAM_SNR = val.split(":")[2].strip()
                            if len(ADSL_UPSTREAM_SNR ) != 0:
                                port_status['ADSL_UPSTREAM_SNR'] = float(ADSL_UPSTREAM_SNR)
                            else:
                                port_status['ADSL_UPSTREAM_SNR'] = 0
                            ADSL_DOWNSTREAM_SNR = val.split(":")[1].split()[0]
                            if len(ADSL_DOWNSTREAM_SNR) != 0:
                                port_status['ADSL_DOWNSTREAM_SNR'] = float(ADSL_DOWNSTREAM_SNR)
                            else:
                                port_status['ADSL_DOWNSTREAM_SNR'] = 0

                        if "DownStream rate" in val:
                            ADSL_CURR_UPSTREAM_RATE = val.split(":")[2].strip()
                            if len(ADSL_CURR_UPSTREAM_RATE) != 0:
                                port_status['ADSL_CURR_UPSTREAM_RATE'] = round(int(ADSL_CURR_UPSTREAM_RATE)/1000000, 2)
                            else:
                                port_status['ADSL_CURR_UPSTREAM_RATE'] = 0
                            ADSL_CURR_DOWNSTREAM_RATE = val.split(":")[1].split()[0]
                            if len(ADSL_CURR_DOWNSTREAM_RATE) != 0:
                                port_status['ADSL_CURR_DOWNSTREAM_RATE'] = round(int(ADSL_CURR_DOWNSTREAM_RATE)/1000000, 2)
                            else:
                                port_status['ADSL_CURR_DOWNSTREAM_RATE'] = 0

                    port_status['TIME'] = datetime.now().strftime('%H:%M:%S')
                    return {'result': port_status, 'status': status.HTTP_200_OK}

                else:
                    return {'result': result['result'], 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

            elif dslam_type == 4:
                result = utility.dslam_port_run_command(dslam_id, 'show linerate', params)

                if result.get('status') == 200:
                    result = result.get('result').split("\n\r")
                    result = [val for val in result if re.search(r'\s+:|--+', val)]

                    port_status = {
                        'ADSL_DOWNSTREAM_SNR': "",
                        'ADSL_UPSTREAM_SNR': "",
                        'ADSL_CURR_DOWNSTREAM_RATE': "",
                        'ADSL_CURR_UPSTREAM_RATE': ""
                    }
                    for inx, val in enumerate(result):
                        if "Stream SNR_Margin" in val:
                            port_status['ADSL_UPSTREAM_SNR'] = float(val.split(":")[1].split("/")[1].split(" ")[0])
                            port_status['ADSL_DOWNSTREAM_SNR'] = float(val.split(":")[1].split("/")[0].strip())

                        if "Rate(D/U)" in val:
                            port_status['ADSL_CURR_UPSTREAM_RATE'] = round(int(val.split(":")[1].split("/")[1].split(" ")[0])/1000, 2)
                            port_status['ADSL_CURR_DOWNSTREAM_RATE'] = round(int(val.split(":")[1].split("/")[0].strip())/1000, 2)
                    port_status['TIME'] = datetime.now().strftime('%H:%M:%S')
                    return {'result': port_status, 'status': status.HTTP_200_OK}

                else:
                    return {'result': result['result'], 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

            elif dslam_type == 5:
                result = utility.dslam_port_run_command(dslam_id, 'show linerate', params)

                if result.get('status') == 200:
                    result = result.get('result').split("\r\n")
                    result = [val.replace("\\t", "    ") for val in result if re.search(r':\s', val)]
                    port_status = {
                        'ADSL_DOWNSTREAM_SNR': "",
                        'ADSL_UPSTREAM_SNR': "",
                        'ADSL_CURR_DOWNSTREAM_RATE': "",
                        'ADSL_CURR_UPSTREAM_RATE': ""
                    }
                    for inx, val in enumerate(result):
                        if "SNR margin" in val:
                            port_status['ADSL_UPSTREAM_SNR'] = float(val.split(":")[1].split()[0])/10
                            port_status['ADSL_DOWNSTREAM_SNR'] = float(val.split(":")[2].strip())/10

                        if "Actual bit rate" in val:
                            port_status['ADSL_CURR_UPSTREAM_RATE'] = round(int(val.split(":")[1].split()[0])/1000, 2)
                            port_status['ADSL_CURR_DOWNSTREAM_RATE'] = round(int(val.split(":")[2].strip())/1000, 2)
                    port_status['TIME'] = datetime.now().strftime('%H:%M:%S')
                    return {'result': port_status, 'status': status.HTTP_200_OK}
                else:
                    return {'result': result['result'], 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

            elif dslam_type == 1:
                result = utility.dslam_port_run_command(dslamObj.pk, 'snmp get port params', params)
                if result.get('status') == 200:
                    return {'result': result['result'], 'status': status.HTTP_200_OK}
                else:
                    return {'result': result, 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}
            elif dslam_type == 2:
                result = utility.dslam_port_run_command(dslam_id, 'show linerate', params)
                if result.get('status') == 200:
                    port_status = {
                        'ADSL_DOWNSTREAM_SNR': "",
                        'ADSL_UPSTREAM_SNR': "",
                        'ADSL_CURR_DOWNSTREAM_RATE': "",
                        'ADSL_CURR_UPSTREAM_RATE': ""
                    }
                    result = result.get('result').split("\r\n")
                    result = [val for val in result if re.search(r'\s{2,}:\s+\d+', val)]
                    for item in result:
                        if 'Upstream' in item and 'SNR' in item:
                            ADSL_UPSTREAM_SNR = item.split(':')[-1].strip()
                            if len(ADSL_UPSTREAM_SNR) != 0:
                                port_status['ADSL_UPSTREAM_SNR'] = float(ADSL_UPSTREAM_SNR)
                            else:
                                port_status['ADSL_UPSTREAM_SNR'] = 0
                        elif 'Downstream' in item and 'SNR' in item:
                            ADSL_DOWNSTREAM_SNR = item.split(':')[-1].strip()
                            if len(ADSL_DOWNSTREAM_SNR) != 0:
                                port_status['ADSL_DOWNSTREAM_SNR'] = float(ADSL_DOWNSTREAM_SNR)
                            else:
                                port_status['ADSL_DOWNSTREAM_SNR'] = 0

                        elif 'Upstream actual' in item:
                            ADSL_CURR_UPSTREAM_RATE = item.split(':')[-1].strip()
                            if len(ADSL_CURR_UPSTREAM_RATE) != 0:
                                port_status['ADSL_CURR_UPSTREAM_RATE'] = round(int(ADSL_CURR_UPSTREAM_RATE)/1000, 2)
                            else:
                                port_status['ADSL_CURR_UPSTREAM_RATE'] = 0
                        elif 'Downstream actual' in item:
                            ADSL_CURR_DOWNSTREAM_RATE = item.split(':')[-1].strip()
                            if len(ADSL_CURR_DOWNSTREAM_RATE) != 0:
                                port_status['ADSL_CURR_DOWNSTREAM_RATE'] = round(int(ADSL_CURR_DOWNSTREAM_RATE)/1000, 2)
                            else:
                                port_status['ADSL_CURR_DOWNSTREAM_RATE'] = 0
                    port_status['TIME'] = datetime.now().strftime('%H:%M:%S')
                    return {'result': port_status, 'status': status.HTTP_200_OK}

                else:
                    return {'result': result['result'], 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}
        except Exception as ex:
            return {'result': str(ex), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

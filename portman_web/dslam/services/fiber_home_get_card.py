from dslam.models import DSLAM
from dslam import utility
import re
import sys, os


class FiberHomeGetCardStatusService:
    def __init__(self, data):
        self.data = data

    @property
    def get_data(self):
        return self.data

    def get_status_cards(self):

        command = 'Show Shelf'
        fqdn = self.data.get('fqdn')
        params = self.data.get('params', None)
        dslam_id = self.data.get('dslam_id', None)

        if dslam_id is None:
            dslam_id = DSLAM.objects.get(fqdn=self.data.get('fqdn')).id
        else:
            dslam_id = DSLAM.objects.get(id=dslam_id).id
            print(DSLAM.objects.get(id=dslam_id).fqdn)

        dslamObj = DSLAM.objects.get(id=dslam_id)
        dslam_type = dslamObj.dslam_type_id
        print(dslam_type)

        try:
            result = utility.dslam_port_run_command(dslamObj.pk, command, params)
            if dslam_type == 3:  ############################## fiberhomeAN3300 ##############################
                result = [val for val in result['result'] if re.search(r'^\s+\d+\s+', val)]
                cards_info = []
                for item in result:
                    print(item)
                    card_info = {}
                    card_info["Card"] = item.split()[0]
                    if 'up' in item:
                        card_info["Status"] = 'ON'
                    else:
                        card_info["Status"] = 'OFF'

                    cards_info.append(card_info)
                cards_info.append({'DslamType': "fiberhomeAN3300"})
                return cards_info

            elif dslam_type == 4:  ############################## fiberhomeAN2200 ##############################
                result = [val for val in result['result'] if re.search(r'^\s+\d+\s+', val)]
                cards_info = []
                for item in result:
                    card_info = {}
                    card_info["Card"] = item.split()[1]
                    if 'MATCH' in item:
                        card_info["Status"] = 'ON'
                    else:
                        card_info["Status"] = 'OFF'

                    cards_info.append(card_info)
                cards_info.append({'DslamType': "fiberhomeAN2200"})
                return cards_info

            elif dslam_type == 5:  ############################## fiberhomeAN5006 ##############################
                if type(result['result']) == str:
                    result['result'] = result['result'].split('\r\n')
                result = [val for val in result['result'] if re.search(r'\s{10,}', val)]
                cards_info = []
                for item in result:
                    card_info = {}
                    card_info["Card"] = item.split()[0]
                    if 'ADSL' in item or 'VDSL' in item:
                        card_info["Status"] = 'ON'
                    else:
                        card_info["Status"] = 'OFF'

                    cards_info.append(card_info)
                cards_info.append({'DslamType': "fiberhomeAN5006"})
                return cards_info
            elif dslam_type == 2:  ############################## Huawei ##############################
                result = [val for val in result['result'] if re.search(r'\s+\d', val)]
                cards_info = []
                for item in result:
                    card_info = {}
                    card_info["Card"] = item.split()[0]
                    if 'Normal' in item:
                        card_info["Status"] = 'ON'
                    else:
                        card_info["Status"] = 'OFF'

                    cards_info.append(card_info)
                cards_info.append({'DslamType': "huawei"})
                return cards_info

            elif dslam_type == 1:  ############################## zyxel ##############################
                if len(result['result']) > 8:
                    result = [item for item in result['result'] if re.search(r'^\s*\d+\s+', item)]
                    cards_info = []

                    for item in result:
                        card_info = {}
                        card_info['Card'] = item.split()[0]
                        if 'active' in item:
                            card_info["Status"] = 'ON'
                        else:
                            card_info["Status"] = 'OFF'

                        cards_info.append(card_info)
                    cards_info.append({'DslamType': "zyxel"})
                    return cards_info
                else:
                    result = utility.dslam_port_run_command(dslamObj.pk, 'cards status', params)
                    result['result'].append({'DslamType': "zyxel"})
                    return result['result']

            elif dslam_type == 7:  ############################## zyxel1248 ##############################
                return [dict(Card='1', Status='ON'), dict(DslamType='zyxel1248')]

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return {'result': 'Error is {0}'.format(ex), 'Line': str(exc_tb.tb_lineno)}

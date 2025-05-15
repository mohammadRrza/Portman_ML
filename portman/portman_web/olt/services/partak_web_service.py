import requests
from olt.models import UsersAuditLog


def save_log(model_name, instance_id, action, description=None):
    return UsersAuditLog.objects.create(
        model_name=model_name,
        instance_id=instance_id,
        action=action,
        description=description,
    )



class PartakApi:
    def __init__(self, model):
        self.object = model
        self.crm_id = None

    def _sendRequest(self, url, payload):
        #print(url, payload, str(payload))
        #return {'text': 'ok!'}
        return requests.request("POST", url, headers={}, data=payload, files=[])

    def _set_crm_id(self):
        self.object.crm_id = self.crm_id
        self.object.save()

    def createCabinet(self):
        try:
            if self.object.is_odc:
                return False
            payload = {
                'ProvinceID': self.object.city.parent.crm_id,
                'CityID': self.object.city.crm_id,
                'Name': self.object.code,
                'IsRent': '0',
                'FqdnCode': self.object.code,
                'Address': '',
                'Active': '1'
            }
            url = "https://my.pishgaman.net/api/pte/regNewFttxMdf"
            response = self._sendRequest(url=url, payload=payload)
            description = f'Create: {response.text}'
            save_log(model_name='Cabinet', instance_id=self.object.id, action='SEND-TO-CRM', description=description)
            self.crm_id = response.json().get('MdfInfo').get('MdfId')
            if response.json().get('ResponseStatus').get('ErrorCode') == 0 and self.crm_id:
                self._set_crm_id()
            return response.json(), payload, url
        except Exception as e:
            print(e)

    def truncate_to_six_decimals(self, number):
        if '.' in number:
            return number[:number.index('.') + 7].ljust(number.index('.') + 7, '0')
        else:
            return number + '.000000'

    def createFAT(self):
        try:
            cabinet_id = self.object.olt.cabinet.crm_id if self.object.olt and self.object.olt.cabinet else 0
            payload = {
                'MdfID': f'{cabinet_id}',
                'FatName': self.object.name,
                'FatNumber': str(self.object.id),
                'NGeoPos': self.truncate_to_six_decimals(self.object.lat),
                'EGeoPos': self.truncate_to_six_decimals(self.object.long),
                'Active': '1' if self.object.is_active else '0'
            }
            url = "https://my.pishgaman.net/api/pte/setFat"
            response = self._sendRequest(url=url, payload=payload)
            description = f'Create: {response.text}'
            save_log(model_name='FAT', instance_id=self.object.id, action='SEND-TO-CRM', description=description)
            return response.json(), payload, url
        except Exception as e:
            print(e)

    def updateFAT(self):
        try:
            cabinet_id = self.object.olt.cabinet.crm_id if self.object.olt and self.object.olt.cabinet else 0
            payload = {
                'MdfID': f'{cabinet_id}',
                'FatNumber': str(self.object.id),
                'Active': '1' if self.object.is_active else '0',
                'FatName': self.object.name,
                'NGeoPos': self.truncate_to_six_decimals(self.object.lat),
                'EGeoPos': self.truncate_to_six_decimals(self.object.long),
            }
            url = "https://my.pishgaman.net/api/pte/updateFat"
            response = self._sendRequest(url=url, payload=payload)
            description = f'Update: {response.text}'
            save_log(model_name='FAT', instance_id=self.object.id, action='SEND-TO-CRM', description=description)
            return response.json(), payload, url
        except Exception as e:
            print(e)

    def deleteFAT(self):
        try:
            url = "https://my.pishgaman.net/api/pte/deleteFat"
            payload = {'FatNumber': str(self.object.id)}
            response = self._sendRequest(url=url, payload=payload)
            description = f'Delete: {response.text}'
            save_log(model_name='FAT', instance_id=self.object.id, action='SEND-TO-CRM', description=description)
            return response.json(), payload, url
        except Exception as e:
            print(e)

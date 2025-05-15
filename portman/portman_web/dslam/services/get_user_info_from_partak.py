import requests
from rest_framework import status
import sys


class GetDataFromPartak:
    def __init__(self):
        pass

    def get_user_info_from_partak(self , username):
        try:
            partak_url = "https://my.pishgaman.net/api/pte/getCustomerAccountInfo?Username=" + username
            partak_response = requests.get(partak_url).json()
            print(partak_response)
            return dict(partak_response)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print({'row': str(ex) + '////' + str(exc_tb.tb_lineno)})
            return {'result': str(ex), 'status': status.HTTP_500_INTERNAL_SERVER_ERROR}

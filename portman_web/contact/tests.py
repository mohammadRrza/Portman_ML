#from django.test import TestCase
from unittest import TestCase
import re, math, requests
from classes.mailer import Mail


class ContactTestCase(TestCase):
    def setUp(self):
        pass

    def test_get_token(self):
        url = "https://monitoring2.pishgaman.net/api_jsonrpc.php"
        body = str({"jsonrpc": "2.0", "id": 1, "method": "user.login",
                    "params": {"user": "software", "password": "ASXRQKD78kykRLT"}}).replace("'", '"')
        print(body)
        response = requests.post(url, headers={"Content-Type": "application/json"}, data=body, verify=False)
        print(response)
        print(response.json())
        print(response.json().get('result'))
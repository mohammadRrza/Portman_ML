import requests
import json


class Ticket:
    def __init__(self, body, title, staff_group_id):
        self.body = body
        self.title = title
        self.staff_group_id = staff_group_id

    def accsess_token(self):
        login_url = 'https://ticketing.pishgaman.net/api/v1/Token/GetToken'
        login_data = str(dict(Username="software", Password="6CJ796MJ8oB",
                              secret="0871EB460075E047A708D830D2F80D10CCBCB30B"))
        response = requests.post(login_url, data=login_data, headers={
            'Content-Type': 'application/json'
        })
        response_json = response.json()
        return response_json['ResultData']['access_token']

    def send_new_ticket(self):
        url = "https://ticketing.pishgaman.net/api/v1/Ticket"
        token = self.accsess_token()

        payload = json.dumps({
            "Title": f"{self.title}",
            "ApplicantId": "f41566a8-d041-4afb-b537-2fa6b2ca4cf2",
            "TemplateAttributeId": "ae9c6745-fd25-454d-9642-21ac497bc998",
            "IsRemoved": "0",
            "SaveMethod": "69e0b98b-185b-434f-be3b-d5d2f550a0ee",
            "Status": "28cb76a6-d999-4ee3-887c-66792287453d",
            "ITStaffGroupID": self.staff_group_id,
            "SubjectList__C": "7e2b589f-4dad-4bd8-aea8-e4618d02aa9c",
            "TicketBody": {
                "TicketBody": {
                    "Body": self.body,
                    "IsPublic": True

                }
            }
        })
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.json()

    def attach_file(self, ticket_id, file_path):
        url = f'https://ticketing.pishgaman.net/api/v1/ticket/{ticket_id}/attachments'
        token = self.accsess_token()
        headers = {
            'Authorization': token,
        }

        with open(file_path, 'rb') as file:
            response = requests.post(url, headers=headers, files={'file': file})

        if response.status_code == 200:
            print("File uploaded successfully.")
        else:
            print("An error occurred while uploading the file.")

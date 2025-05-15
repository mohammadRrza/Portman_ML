from json import dumps as serializer
from requests.sessions import Session
from json import loads as deserializer
import re

class BlockedListService:
    IBS_URI = 'http://172.28.238.164:1237/'
    USERNAME = 'Portman'
    PASSWORD = 'qazwsx0o1mVz7'
    DEFAULT_HEADERS = {
        "Content-type": "application/json",
        "Accept": "application/json",
        "User-Agent": "ibs-jsonrpc",
        "Accept-Charset": "utf-8",
        "Cache-Control": "no-cache",
    }
    _session = None

    def _get_session(self):
        if self._session is None:
            self._session = Session()
            self._session.headers.update(self.DEFAULT_HEADERS)
        return self._session

    def send_request(self, handler, method, parameters):
        session = self._get_session()
        method_to_call = ".".join((handler, method,))
        try:
            response_object = session.post(url=self.IBS_URI, data=serializer(
                dict(method=method_to_call, jsonrpc="2.0", params=parameters)), timeout=5)


        except:
            print("connection to IBS Failed!")
            return False

        return deserializer(response_object.text)

    def get_advertiser_chakavak_info(self, user_name):
            handler = "user"
            method = "getUserInfo"
            params = {
                "auth_name": self.USERNAME,
                "auth_pass": self.PASSWORD,
                "auth_type": "ADMIN",
                "voip_username": user_name
            }
            resp = self.send_request(handler, method, params)
            return resp
    
    def get_blocked_list(self, advertiser):
        try:
            advertiser_data = self.get_advertiser_chakavak_info(str(advertiser.contact_number))
            if advertiser_data.get('error'):
                return dict(err=advertiser_data.get('error'))
            result = advertiser_data.get("result", {})
            existing_blocked_in = []
            existing_blocked_out = []
            custom_field_blocked_in_count = 0
            custom_field_blocked_out_count = 0
            for user_id, user_data in result.items():
                attrs = user_data.get("attrs", {})

                for key, value in attrs.items():
                    if key.startswith("custom_field_blocked_in") and value:
                        existing_blocked_in.extend(value.split(","))
                        max_count = re.findall(r'\d+', key)
                        custom_field_blocked_in_count = int(max_count[0]) if max_count and int(max_count[0]) > custom_field_blocked_in_count else custom_field_blocked_in_count
                    elif key.startswith("custom_field_blocked_out") and value:
                        existing_blocked_out.extend(value.split(","))
                        max_count = re.findall(r'\d+', key)
                        custom_field_blocked_out_count = int(max_count[0]) if max_count and int(max_count[0]) > custom_field_blocked_out_count else custom_field_blocked_out_count

            existing_blocked_in = list(dict.fromkeys(num.strip() for num in existing_blocked_in if num.strip()))
            existing_blocked_out = list(dict.fromkeys(num.strip() for num in existing_blocked_out if num.strip()))

            return dict(blocked_in=existing_blocked_in,
                        blocked_out=existing_blocked_out,
                        custom_field_blocked_in_count=custom_field_blocked_in_count,
                        custom_field_blocked_out_count=custom_field_blocked_out_count,
                        err=None)
        except:
            return dict(err="Connection to IBS Failed!")

    def set_blocked_list(self, advertiser, blocked_in: list, blocked_out: list, action: str):
        state = False
        handler = "user"
        method = "updateUserAttrs"
        blocked_list = self.get_blocked_list(advertiser)
        if blocked_list.get('err'):
            return state, blocked_list.get('err')
        existing_blocked_in = blocked_list.get("blocked_in", [])
        existing_blocked_out = blocked_list.get("blocked_out", [])
        custom_field_blocked_in_count = blocked_list.get("custom_field_blocked_in_count", 0)
        custom_field_blocked_out_count = blocked_list.get("custom_field_blocked_out_count", 0)

        if action.lower() == "add":
            updated_blocked_in = list(dict.fromkeys(blocked_in + existing_blocked_in))
            updated_blocked_out = list(dict.fromkeys(blocked_out + existing_blocked_out))
        elif action.lower() == "delete":
            updated_blocked_in = [item for item in existing_blocked_in if item not in blocked_in]
            updated_blocked_out = [item for item in existing_blocked_out if item not in blocked_out]
        else:
            err = "Please enter a valid action!"
            return state, err

        def chunk_list(lst, chunk_size=150):
            return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

        custom_fields = {}

        if blocked_in:
            chunks_in = chunk_list(updated_blocked_in)
            for idx in range(0, custom_field_blocked_in_count+1):
                key = "custom_field_blocked_in" if idx == 0 else f"custom_field_blocked_in_{idx}"
                custom_fields[key] = ''
            for idx, chunk in enumerate(chunks_in):
                key = "custom_field_blocked_in" if idx == 0 else f"custom_field_blocked_in_{idx}"
                custom_fields[key] = ','.join(chunk)


        if blocked_out:
            chunks_out = chunk_list(updated_blocked_out)
            for idx in range(0, custom_field_blocked_out_count+1):
                key = "custom_field_blocked_out" if idx == 0 else f"custom_field_blocked_out_{idx}"
                custom_fields[key] = ''
            for idx, chunk in enumerate(chunks_out):
                key = "custom_field_blocked_out" if idx == 0 else f"custom_field_blocked_out_{idx}"
                custom_fields[key] = ','.join(chunk)

        params = {
            "auth_name": self.USERNAME,
            "auth_pass": self.PASSWORD,
            "auth_type": "ADMIN",
            "user_id": str(advertiser.chakavak_id),
            "attrs": {
                "custom_fields": [custom_fields, []],
            },

            "to_del_attrs": [],
        }

        resp = self.send_request(handler, method, params)
        print(params)
        print(resp)
        err = resp.get('error')
        if err is None:
            state = True

        return state, err

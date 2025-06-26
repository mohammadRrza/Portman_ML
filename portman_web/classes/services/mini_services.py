import json

import requests


def get_token_from_api_pishgaman():
    login_url = "http://api.pishgaman.net/gateway/token"
    headers = {"Content-Type": "application/json",
               "Authorization": "Basic b3NzLXBvcnRtYW46eTJ2UGowVntjeXRlQVNRcUpufH5mRnRzL1BXP3F9MSo=",
               "appid": "57"}
    try:
        response = requests.get(login_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        token = response_json['Result']
        return token
    except requests.exceptions.RequestException as e:
        raise Exception("Failed to retrieve API token.") from e


def validate_postal_code(postal_code):
    if not postal_code.isdigit() or len(postal_code) != 10:
        return False
    return True


def convert_postal_code(url, postal_code, token):
    try:
        if not validate_postal_code(postal_code):
            return dict(result="postal_code must be a 10-digit number.", status=400)
        postal_code = json.dumps([postal_code])
        response = requests.get(
            url, 
            data=postal_code,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                "appid": "57"
            },
            timeout=5
        )
        response_json = response.json()

        if response_json.get('OperationResultCode', None) == 200:
            result = response_json.get('Result')[0]
            return dict(result=result, status=200)
        elif response_json.get('OperationResultDescription', None) == 'Invalid postal code':
            result = 'The postal code is not available in the postal code bank'
            return dict(result=result, status=404)
        else:
            return dict(result='An error has occurred', status=500)
    except requests.exceptions.Timeout:
        return dict(result="The request has timed out, please try again later.", status=408)
    except requests.exceptions.RequestException as e:
        return dict(result=f"An error occurred: {e}", status=500)


def convert_postal_code_to_geo_coordinate(postal_code):
    url = "http://api.pishgaman.net/gateway/services/gnaf/positions"
    token = get_token_from_api_pishgaman()
    response = convert_postal_code(url, postal_code, token)
    return response


def convert_postal_code_to_address(postal_code):
    url = "http://api.pishgaman.net/gateway/services/gnaf/addresses"
    token = get_token_from_api_pishgaman()
    response = convert_postal_code(url, postal_code, token)
    return response

def get_shortner_link_approval_code(mobileNumber, token=None):
    url = 'http://api.pishgaman.net/gateway/services/token'
    payload = json.dumps({'username': mobileNumber})
    token = token if token else get_token_from_api_pishgaman()
    response = requests.post(
        url, 
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            "appid": "57"
        },
        timeout=5
    )
    response_json = response.json()
    if response_json.get('OperationResultCode', None) == 200:
        result = response_json.get('Result')
        return True, result

    return False, ""

def shortner_link(longLink, mobileNumber = None):
    url = 'http://api.pishgaman.net/gateway/services/shortlinkotp'
    payload = json.dumps({'Link':longLink, 'Userkey': mobileNumber.lstrip("0")})
    token = get_token_from_api_pishgaman()
    response = requests.post(
        url, 
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            "appid": "57"
        },
        timeout=5
    )
    response_json = response.json()
    #print(response.headers, response_json)

    if response_json.get('OperationResultCode', None) == 200:
        result = response_json.get('Result')
        return True, result.get('shortlink'), str(result.get('verificationCode'))

    return False, "", None
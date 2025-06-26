import jwt

class PortmanUtils():

    @staticmethod
    def decode_token(request):
        user_token = request.META.get('HTTP_AUTHORIZATION').split()[1]
        decoded_token = jwt.decode(jwt=user_token.encode('utf-8'),verify=False,)
        return decoded_token
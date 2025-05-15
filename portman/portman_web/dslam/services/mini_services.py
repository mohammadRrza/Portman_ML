from users.models import User

def retrieve_allowed_dslams(user):
    # model_user = User(type=user.type)
    # model_user.set_user_id(user.id)
    allowed_dslams = user.get_allowed_dslams()
    return allowed_dslams
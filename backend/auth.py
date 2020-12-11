from secrets import token_hex

from flask import request

user_tokens = {}


def user_authenticated():
    user_id = request.cookies.get('user_id')
    session_token = request.cookies.get('session_token')
    if user_id and session_token:
        if user_tokens.get(str(user_id), None) == session_token:
            return True
    return False


def add_user_token(user_id):
    user_tokens[str(user_id)] = token_hex(16)


def get_user_token(user_id):
    return user_tokens[str(user_id)]


def remove_user_token(user_id):
    del user_tokens[str(user_id)]

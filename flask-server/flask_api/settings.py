import os
from flask import Flask, jsonify, request
from functools import wraps
from flask_api.views import not_found_view
import datetime
import jwt

templates_dir = os.path.abspath('templates')
static_dir = os.path.abspath('static')

server = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)

@server.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', True)
    response.headers.add('Access-Control-Allow-Headers', 'ContentType,Authorization,Accepts')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@server.errorhandler(404)
def page_not_found(e):
    return not_found_view()

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']

            if not token:
                return jsonify({'response': 'token is missing'})
            try:
                data = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])
                if datetime.datetime.now() > datetime.datetime.fromisoformat(data["expires"]):
                    return jsonify({'response': 'token has expired'})
            except:
                return jsonify({'response': 'token invalid'})

        return f(data["user-id"], data["username"], data["admin"], *args, **kwargs)
    return decorator

# will not end the session if a token isn't available, just checks to see if one is there
# checks the cookies, only used for pages that don't require particularly good security
# just for ones that require some kind of user identification
def soft_token_check(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.cookies.get('token')

        if not token or token == "null":
            # no cookie found
            return f(-1, "", 0, *args, **kwargs)

        data = jwt.decode(token, server.config['SECRET_KEY'], algorithms=['HS256'])

        if "user-id" not in data or "username" not in data or "admin" not in data:
            # invalid cookie
            return f(-1, "", 0, *args, **kwargs)

        if datetime.datetime.now() > datetime.datetime.fromisoformat(data["expires"]):
            # token has expired
            return f(-1, "", 0, *args, **kwargs)

        return f(data["user-id"], data["username"], data["admin"], *args, **kwargs)
    return decorator
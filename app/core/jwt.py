import os
from functools import wraps
import jwt
from dotenv import load_dotenv
from flask import request, jsonify, g

from app.repo.user_repo import UserRepo

load_dotenv()


JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

user_repo = UserRepo()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            print(data)
            user_id = data['userid']
            try:
                user = user_repo.get_user_by_user_id(user_id)
            except Exception as e:
                return jsonify({'message': 'Connection error'}), 500
            if not user:
                return jsonify({"message": "User not found"}), 401
            # 将用户信息存储到全局对象g中
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Toekn has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(*args, **kwargs)
    return decorated


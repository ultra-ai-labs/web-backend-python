import os
import random
import string
from datetime import datetime, timedelta
import jwt
import bcrypt

from app.repo.user_repo import User, UserRepo
from tools import next_id

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_EXPIRATION_DELTA = timedelta(days=90)

user_repo = UserRepo()


def generate_token(user_id):
    payload = {
        'userid': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    bearer_token = f"Bearer {token}"
    print(bearer_token)

    return token


def generate_password_hash(password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # print(hashed_password)
    return hashed_password


def create_user(user_id, username, password, email=None):
    new_User = User(
        user_id=user_id,
        username=username,
        password=generate_password_hash(password),
        email=email
    )
    user_repo.session.add(new_User)
    user_repo.session.commit()


def generate_random_password(length=6):
    return ''.join(random.choices(string.digits, k=length))

def create_test_users(start_num, end_num):
    for i in range(start_num, end_num):
        test_userid = next_id()
        username = f"测试{i}号"
        password = generate_random_password()
        create_user(test_userid, username, password)
        print(f"账号: {username}, 密码: {password}")

create_test_users(20, 100)

# test_userid = next_id()
# username = "测试3号"

# password = "123456"
# generate_password_hash(password)

# create_user(test_userid, username, password)

# generate_token("469183722814570496")


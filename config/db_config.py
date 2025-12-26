import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

load_dotenv()
# 获取当前环境
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")


# redis config
REDIS_DB_HOST = "127.0.0.1"  # your redis host
REDIS_DB_PWD = os.getenv("REDIS_DB_PWD", "123456")  # your redis password

# 数据库配置
if ENVIRONMENT == "production":
    DB_USER = os.getenv("PROD_DB_USER", "root")
    DB_PWD = os.getenv("PROD_DB_PWD", "")
    DB_URI = os.getenv("PROD_DB_URI", "127.0.0.1")
    DB_PORT = os.getenv("PROD_DB_PORT", "3306")
    DB_NAME = os.getenv("PROD_DB_NAME", "media_crawler")
else:
    DB_USER = os.getenv("DEV_DB_USER", "root")
    DB_PWD = os.getenv("DEV_DB_PWD", "")
    DB_URI = os.getenv("DEV_DB_URI", "127.0.0.1")
    DB_PORT = os.getenv("DEV_DB_PORT", "3306")
    DB_NAME = os.getenv("DEV_DB_NAME", "media_crawler")
    print(DB_USER, DB_PWD, DB_URI, DB_PORT, DB_NAME)


# mysql config
DEV_USER_DB_PWD = os.getenv("DEV_USER_DB_PWD", "")  # your relation db password
DEV_USER_DB_USER = os.getenv("DEV_USER_DB_USER", "root")
DEV_USER_DB_URI = os.getenv("DEV_USER_DB_URI", "127.0.0.1")
DEV_USER_DB_PORT = os.getenv("DEV_USER_DB_PORT", "3306")
DEV_USER_DB_NAME = os.getenv("DEV_USER_DB_NAME", "media_crawler")

RELATION_DB_URL = f"mysql://{DB_USER}:{DB_PWD}@{DB_URI}:{DB_PORT}/{DB_NAME}"
PYMYSQL_PROD_DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_URI}:{DB_PORT}/{DB_NAME}"

DEV_USER_DB_URL = f"mysql+pymysql://{DEV_USER_DB_USER}:{DEV_USER_DB_PWD}@{DEV_USER_DB_URI}:{DEV_USER_DB_PORT}/{DEV_USER_DB_NAME}"
user_engine = create_engine(
    DEV_USER_DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=360000,  # Recycle connections after 30 minutes
    pool_pre_ping=True
    )
UserSession = sessionmaker(bind=user_engine)


def get_session():
    session = None
    retries = 5
    while retries > 0:
        try:
            session = UserSession()
            break
        except exc.OperationalError as e:
            print(f"Connection failed, retrying... {retries} retries left")
            time.sleep(5)  # Wait before retrying
            retries -= 1

    if session is None:
        raise Exception("Could not establish a database connection after multiple retries")
    return session

# sqlite3 config
# RELATION_DB_URL = f"sqlite://data/media_crawler.sqlite"
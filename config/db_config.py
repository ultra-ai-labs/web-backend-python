import os
import time
import urllib.parse
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


# Direct use of RELATION_DB_URL from environment variable if available, as requested.
# WARNING: This assumes the URL in .env is already correctly formatted and URL-encoded if necessary.
RELATION_DB_URL_ENV = os.getenv("RELATION_DB_URL")

if RELATION_DB_URL_ENV:
    # If the user explicitly provides RELATION_DB_URL in .env, use it directly.
    # Note: SQLAlchemy requires 'mysql+pymysql://' driver for pymysql.
    # If the env var is 'mysql://', we might need to adjust it to 'mysql+pymysql://'
    # or rely on sqlalchemy's default driver detection (which might not be pymysql).
    # To be safe and compatible with previous logic, we ensure it uses pymysql driver.
    if RELATION_DB_URL_ENV.startswith("mysql://"):
         SQLALCHEMY_DATABASE_URI = RELATION_DB_URL_ENV.replace("mysql://", "mysql+pymysql://", 1)
    else:
         SQLALCHEMY_DATABASE_URI = RELATION_DB_URL_ENV
else:
    # Fallback to constructing from components if RELATION_DB_URL is not set
    # URL encode password to handle special characters like '@'
    DB_PWD_ENCODED = urllib.parse.quote_plus(DB_PWD)
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PWD_ENCODED}@{DB_URI}:{DB_PORT}/{DB_NAME}"

# Keep these for compatibility
RELATION_DB_URL = SQLALCHEMY_DATABASE_URI
PYMYSQL_PROD_DB_URL = SQLALCHEMY_DATABASE_URI
DEV_USER_DB_URL = SQLALCHEMY_DATABASE_URI

user_engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
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

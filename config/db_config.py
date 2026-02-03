import os
import time
import urllib.parse
from urllib.parse import urlparse, quote_plus
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


def parse_and_reconstruct_url(mysql_url):
    """
    Parse the MySQL URL manually to handle special characters in passwords (like '@')
    and reconstruct it with proper encoding for SQLAlchemy.
    """
    if not mysql_url:
        return None
        
    try:
        # If there are multiple '@', it means the password contains '@'
        # Format: mysql://user:password@host:port/dbname
        if mysql_url.count("@") > 1:
            # Find the last '@' which separates credentials from host
            last_at_index = mysql_url.rfind("@")
            
            # Everything before the last '@' contains user:password
            credentials_part = mysql_url[:last_at_index]
            host_part = mysql_url[last_at_index+1:]
            
            # Find the scheme (e.g., mysql://)
            scheme_end = credentials_part.find("://")
            if scheme_end != -1:
                scheme = credentials_part[:scheme_end+3]
                user_pass = credentials_part[scheme_end+3:]
                
                # Split user and password
                if ":" in user_pass:
                    user, password = user_pass.split(":", 1)
                    # Encode the password
                    password_encoded = quote_plus(password)
                    # Reconstruct the URL
                    return f"{scheme}{user}:{password_encoded}@{host_part}"
        
        return mysql_url
    except Exception as e:
        print(f"Error parsing RELATION_DB_URL: {e}")
        return mysql_url

# Direct use of RELATION_DB_URL from environment variable if available, as requested.
RELATION_DB_URL_ENV = os.getenv("RELATION_DB_URL")

if RELATION_DB_URL_ENV:
    # 1. Fix special characters encoding
    fixed_url = parse_and_reconstruct_url(RELATION_DB_URL_ENV)
    
    # 2. Fix driver for SQLAlchemy (needs mysql+pymysql://)
    if fixed_url.startswith("mysql://"):
         SQLALCHEMY_DATABASE_URI = fixed_url.replace("mysql://", "mysql+pymysql://", 1)
    else:
         SQLALCHEMY_DATABASE_URI = fixed_url
else:
    # Fallback to constructing from components
    DB_PWD_ENCODED = urllib.parse.quote_plus(DB_PWD)
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PWD_ENCODED}@{DB_URI}:{DB_PORT}/{DB_NAME}"

# Keep these for compatibility
RELATION_DB_URL = SQLALCHEMY_DATABASE_URI
PYMYSQL_PROD_DB_URL = SQLALCHEMY_DATABASE_URI
DEV_USER_DB_URL = SQLALCHEMY_DATABASE_URI

user_engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_size=3,
    max_overflow=5,
    pool_timeout=20,
    pool_recycle=600,  # 10分钟回收一次
    pool_pre_ping=True,
    echo_pool=False,
    connect_args={
        'charset': 'utf8mb4',
        'connect_timeout': 5,
        'read_timeout': 30,
        'write_timeout': 30
    }
    )
UserSession = sessionmaker(bind=user_engine)


def get_session():
    session = None
    retries = 3
    while retries > 0:
        try:
            session = UserSession()
            # 测试连接是否有效
            session.execute('SELECT 1')
            session.commit()
            break
        except (exc.OperationalError, exc.DBAPIError) as e:
            if session:
                session.rollback()
                session.close()
                session = None
            print(f"Connection failed, retrying... {retries} retries left: {e}")
            time.sleep(1)
            retries -= 1
        except Exception as e:
            if session:
                session.rollback()
                session.close()
            raise e

    if session is None:
        raise Exception("Could not establish a database connection after multiple retries")
    return session

# sqlite3 config
# RELATION_DB_URL = f"sqlite://data/media_crawler.sqlite"

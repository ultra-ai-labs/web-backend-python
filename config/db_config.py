import os
import time
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Redis config
REDIS_DB_HOST = os.getenv("REDIS_DB_HOST")
REDIS_DB_PWD = os.getenv("REDIS_DB_PWD")

# Database Config
# Priority: RELATION_DB_URL from env > Constructed from env components
# We do NOT provide default values like 'localhost' or 'root'.
# Users must define these in their environment variables (e.g. .env file).

RELATION_DB_URL_ENV = os.getenv("RELATION_DB_URL")

# Components from env
DB_USER = os.getenv("DB_USER")
DB_PWD = os.getenv("DB_PWD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

RELATION_DB_URL = None

if RELATION_DB_URL_ENV:
    # Use the provided URL
    RELATION_DB_URL = RELATION_DB_URL_ENV
    
    # Handle potentially unescaped '@' in password within the URL
    if "@" in RELATION_DB_URL_ENV:
        try:
             # Basic attempt to parse manually if standard parsing fails due to multiple '@'
             last_at_index = RELATION_DB_URL_ENV.rfind("@")
             
             credentials_part = RELATION_DB_URL_ENV[:last_at_index]
             host_part = RELATION_DB_URL_ENV[last_at_index+1:]
             
             scheme_end = credentials_part.find("://")
             if scheme_end != -1:
                 scheme = credentials_part[:scheme_end+3]
                 user_pass = credentials_part[scheme_end+3:]
                 
                 if ":" in user_pass:
                     user, password = user_pass.split(":", 1)
                     if password == urllib.parse.unquote_plus(password):
                         password_encoded = urllib.parse.quote_plus(password)
                         RELATION_DB_URL = f"{scheme}{user}:{password_encoded}@{host_part}"
        except Exception as e:
            print(f"Error parsing/fixing RELATION_DB_URL: {e}")
            RELATION_DB_URL = RELATION_DB_URL_ENV

elif all([DB_USER, DB_PWD, DB_HOST, DB_PORT, DB_NAME]):
    # Construct from components if all are present
    encoded_pwd = urllib.parse.quote_plus(DB_PWD)
    RELATION_DB_URL = f"mysql://{DB_USER}:{encoded_pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

else:
    # No valid configuration found
    raise ValueError(
        "Database configuration is missing! "
        "You must set either 'RELATION_DB_URL' OR all of ('DB_USER', 'DB_PWD', 'DB_HOST', 'DB_PORT', 'DB_NAME') "
        "in your environment variables (e.g. .env file)."
    )

# SQLAlchemy URL (needs pymysql driver specified usually)
if RELATION_DB_URL.startswith("mysql://") and "pymysql" not in RELATION_DB_URL:
     PYMYSQL_PROD_DB_URL = RELATION_DB_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
     PYMYSQL_PROD_DB_URL = RELATION_DB_URL

# Create engine (used by synchronous code)
user_engine = create_engine(
    PYMYSQL_PROD_DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=360000,
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
            time.sleep(5)
            retries -= 1

    if session is None:
        raise Exception("Could not establish a database connection after multiple retries")
    return session

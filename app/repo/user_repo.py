from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, BigInteger, exc
from sqlalchemy.orm import sessionmaker

from config import get_session

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    # match actual schema: user_id varchar(64), create_time/update_time bigint
    user_id = Column(String(64), primary_key=True)
    username = Column(String(64), unique=True)
    password = Column(String(255))
    email = Column(String(128), unique=False)
    expire_time = Column(BigInteger)
    create_time = Column(BigInteger)
    update_time = Column(BigInteger)


class UserRepo:
    def __init__(self):
        # Do NOT create a session here to avoid threading issues
        pass

    def get_user_by_username(self, username):
        session = get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            # Detach object from session so it can be used after session closes
            if user:
                session.expunge(user)
            return user
        except exc.OperationalError as e:
            print("OperationalError: ", e)
            # Retry once
            session.close()
            session = get_session()
            user = session.query(User).filter_by(username=username).first()
            if user:
                session.expunge(user)
            return user
        except Exception as e:
            print(f"Error getting user by username {username}: {e}")
            return None
        finally:
            session.close()

    def get_user_by_user_id(self, user_id):
        session = get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                session.expunge(user)
            return user
        except exc.SQLAlchemyError as e:
            print("DBError: ", e)
            session.close()
            session = get_session()
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                session.expunge(user)
            return user
        except Exception as e:
            print(f"Error getting user by user_id {user_id}: {e}")
            return None
        finally:
            session.close()

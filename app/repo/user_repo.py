from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, exc
from sqlalchemy.orm import sessionmaker

from config import get_session

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(255))
    email = Column(String(100), unique=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UserRepo:
    def __init__(self):
        self.session = get_session()

    def get_user_by_username(self, username):
        try:
            return self.session.query(User).filter_by(username=username).first()
        except exc.OperationalError as e:
            print("OperationalError: ", e)
            self.session = get_session()
            return self.session.query(User).filter_by(username=username).first()

    def get_user_by_user_id(self, user_id):
        try:
            return self.session.query(User).filter_by(user_id=user_id).first()
        except exc.SQLAlchemyError as e:
            print("DBError: ", e)
            self.session = get_session()
            return self.session.query(User).filter_by(user_id=user_id).first()

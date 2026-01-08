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
        self.session = get_session()

    def refresh_session(self):
        """Refresh session to see committed changes from other sessions"""
        try:
            self.session.rollback()
            self.session.expire_all()
            print("[UserRepo.refresh_session] cache refreshed")
        except Exception as e:
            print(f"[UserRepo.refresh_session] error: {e}")

    def get_user_by_username(self, username):
        try:
            # Only expire_all - refresh_session is called after create/update
            self.session.expire_all()
            user = self.session.query(User).filter_by(username=username).first()
            return user
        except exc.OperationalError as e:
            print("OperationalError: ", e)
            self.session = get_session()
            return self.session.query(User).filter_by(username=username).first()

    def get_user_by_user_id(self, user_id):
        try:
            self.session.expire_all()
            return self.session.query(User).filter_by(user_id=user_id).first()
        except exc.SQLAlchemyError as e:
            print("DBError: ", e)
            self.session = get_session()
            return self.session.query(User).filter_by(user_id=user_id).first()

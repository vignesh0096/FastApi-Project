from sqlalchemy import Column, Integer, String
from db import Base


class Users(Base):
    __tablename__ = "UserData"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String(255))
    phone_no = Column(String(255))
    email = Column(String(255))
    password = Column(String(255))
    place = Column(String(255))


class LoginDetails(Base):
    __tablename__ = 'loginDetails'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255))
    password = Column(String(255))
    timezone = Column(String(255))


class GenerateOtp(Base):
    __tablename__ = "Verification"

    id = Column(Integer,primary_key=True,index=True)
    phone_no = Column(String(255))
    otp = Column(String(100))
    authentication = Column(Integer,default=0)

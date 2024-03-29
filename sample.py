from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import models
from sqlalchemy import desc
from db import engine, Session_local,get_db
from sqlalchemy.orm import Session
from otp import get_otp
from datetime import datetime
import bcrypt
from auth_handler import *
from auth_bearer import *


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


class Create_user(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    phone_no : str = Field(min_length=1,max_length=100)
    email: str = Field(min_length=1,max_length=100)
    password: str = Field(min_length=1,max_length=255)
    place: str = Field(min_length=1,max_length=100)


class Otp(BaseModel):
    phone_no: str = Field(min_length=1,max_length=100)


class Login(BaseModel):
    email: str = Field(min_length=1,max_length=100)
    password: str = Field(min_length=1,max_length=100)


user_list = []


# @app.get("/")
# def read_me(db:Session = Depends(get_db)):
#     return db.query(models.Users).all()


@app.get("/{user_id}")
def get(user_id : int,db:Session = Depends(get_db)):
    user_detail = db.query(models.Users).filter(models.Users.id == user_id).first()
    return user_detail


@app.post("/generate")
def generate(num: Otp,db:Session = Depends(get_db)):
    try:
        number = models.GenerateOtp()
        otp = get_otp(num.phone_no)
        number.phone_no = num.phone_no
        number.otp = otp
        number.authentication = 0
        db.add(number)
        db.commit()
        return "Otp send successfully"
    except Exception as e:
        raise HTTPException(status_code=404,detail="enter valid number")


@app.put("/verification{otp}")
def verify(otp : str,db:Session = Depends(get_db)):
    verification = db.query(models.GenerateOtp).filter(models.GenerateOtp.otp == otp).first()
    print(verification)
    if verification is None :
        raise HTTPException(status_code=404,
                            detail=f"the otp {otp} you have entered is incorrect")
    verification.authentication = 1
    db.add(verification)
    db.commit()
    return "otp verified successfully"


@app.post("/")
def create(user: Create_user,db:Session = Depends(get_db)):
    try:
        user_details = models.Users()
        check = db.query(models.GenerateOtp).filter(models.GenerateOtp.phone_no == user.phone_no).first()
        if check.authentication == 1 and check.phone_no == user.phone_no:
            user_details.name = user.name
            user_details.email = user.email
            password = user.password
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user_details.password = hashed
            user_details.phone_no = user.phone_no
            user_details.place = user.place
            db.add(user_details)
            db.commit()
        return user
    except Exception as e:
        raise HTTPException(status_code=404,detail=str(e))


@app.post('/login')
def login(user:Login,db:Session = Depends(get_db)):
    try:
        token = ''
        user_details = models.LoginDetails()
        check = db.query(models.Users).filter(models.Users.email == user.email).first()
        if check is None:
            raise HTTPException(status_code=404,detail="email id not registered")
        password = user.password
        hashed_password = check.password
        if not bcrypt.checkpw(password.encode('utf-8'),hashed_password.encode('utf-8')):
            raise HTTPException(status_code=401,detail="enter valid password")
        else:
            user_details.email = user.email
            token = signJWT(check.id)
            user_details.token = token['access_token']
            user_details.timezone = str(datetime.now())
            db.add(user_details)
            db.commit()

        # else:
        #     raise HTTPException(status_code=401,detail="Enter valid password")
        return f"token : {token['access_token']}"
    except:
        raise HTTPException(status_code=404,detail="Something went wrong please try again")


@app.put('/logout')
def logout(email:str,db:Session = Depends(get_db)):
    query = (db.query(models.LoginDetails)
             .filter(models.LoginDetails.email == email)
             .order_by(desc(models.LoginDetails.timezone))).first()
    if query:
        query.token = ''
        db.add(query)
        db.commit()
        return "logged out successfully"
    return "Something went wrong"


@app.put('/{user_id}',dependencies=[Depends(JWTBearer())])
def edit(user_id : int, user:Create_user,db:Session = Depends(get_db)):
    user_details = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_details is None:
        raise HTTPException(status_code=404,
                            detail=f"user id {user_id} does not exist")
    user_details.name = user.name
    user_details.phone_no = user.phone_no
    user_details.email = user.email
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'),bcrypt.gensalt())
    user_details.password = hashed_password
    user_details.place = user.place
    db.add(user_details)
    db.commit()
    return f"user id {user_id} has been successfully updated"


@app.delete('/{user_id}',dependencies=[Depends(JWTBearer())])
def delete(user_id: int,db: Session = Depends(get_db)):
    del_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if del_user is None:
        raise HTTPException(status_code=404,
                            detail=f"user id {user_id} does not exist")
    db.query(models.Users).filter(models.Users.id == user_id).delete()
    db.commit()
    return f"user id {user_id} has been deleted successfully"

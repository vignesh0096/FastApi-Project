from fastapi import FastAPI,HTTPException,Depends
from pydantic import BaseModel,Field
from uuid import UUID
import models
from db import engine,Session_local
from sqlalchemy.orm import Session
from otp import get_otp
from datetime import datetime
import bcrypt


app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = Session_local()
        yield db
    finally:
        db.close()


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
# class VerifyOtp(BaseModel):
#     phone_no: str = Field(min_length=1, max_length=100)
#     otp: str = Field(min_length=1,max_length=100)
#     authentication: int = Field(lt=-1,gt=1)


user_list = []


@app.get("/")
def read_me(db:Session = Depends(get_db)):
    return db.query(models.Users).all()


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
        user_details = models.LoginDetails()
        check = db.query(models.Users).filter(models.Users.email == user.email).first()
        print(check.password)
        if check is None:
            raise HTTPException(status_code=404,detail="email id not registered")
        password = user.password
        hashed_password = check.password
        if bcrypt.checkpw(password.encode('utf-8'),hashed_password.encode('utf-8')):
            user_details.email = user.email
            user_details.password = check.password
            user_details.timezone = str(datetime.now())
            db.add(user_details)
            db.commit()
        # else:
        #     raise HTTPException(status_code=401,detail="Enter valid password")
        return "logged in successfully"
    except:
        raise HTTPException(status_code=404,detail="Something went wrong please try again")


@app.put('/{user_id}')
def edit(user_id : int, user:Create_user,db:Session = Depends(get_db)):
    user_details = db.query(models.Users).filter(models.Users.id == user_id).first()
    if user_details is None:
        raise HTTPException(status_code=404,
                            detail=f"user id {user_id} does not exist")
    user_details.name = user.name
    user_details.phone_no = user.phone_no
    user_details.email = user.email
    user_details.password = user.password
    user_details.place = user.places
    db.add(user_details)
    db.commit()
    return f"user id {user_id} has been successfully updated"


@app.delete('/{user_id}')
def delete(user_id : int,db:Session = Depends(get_db)):
    del_user = db.query(models.Users).filter(models.Users.id == user_id).first()
    if del_user is None:
        raise HTTPException(status_code=404,
                            detail=f"user id {user_id} does not exist")
    db.query(models.Users).filter(models.Users.id == user_id).delete()
    db.commit()
    return f"user id {user_id} has been deleted successfully"
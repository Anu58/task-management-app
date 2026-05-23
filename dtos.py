from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    name: str
    username: str
    email: str
    password: str


class UserResponseSchema(BaseModel):
    name: str
    username: str
    email: str
    id: int

class LoginSchema(BaseModel):
    
    username: str
    password: str

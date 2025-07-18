from pydantic import BaseModel, EmailStr, Field, constr


class LoginRequest(BaseModel):
    email: EmailStr = Field(...,
        examples=["alice@example.com"],
        description="이메일 주소"
    )
    password: str = Field(...,
        min_length=4,
        max_length=300,
        examples=["alice123"],
        description="비밀번호"
    )

SignupRequest = LoginRequest

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)
    new_password: str

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)

if __name__ == '__main__':
    login = LoginRequest(email='ncubeteam1@gmail.com', password='<PASSWORD>')
    print(login)
    print(login.model_dump(), type(login.model_dump()))
    print(len(login.email), len(login.password))

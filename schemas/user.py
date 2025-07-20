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
    email: EmailStr = Field(..., examples=["alice@example.com"], description="이메일 주소")


class PasswordResetConfirm(BaseModel):
    email: EmailStr = Field(..., examples=["alice@example.com"], description="이메일 주소")
    code: constr(min_length=6, max_length=6) = Field(..., description="이메일로 보낸 인증 코드 6자리")
    new_password: str = Field(...,
                              min_length=4,
                              max_length=300,
                              examples=["alice123"],
                              description="비밀번호"
                              )


class EmailVerificationRequest(BaseModel):
    email: EmailStr = Field(..., examples=["alice@example.com"], description="이메일 주소")


class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6) = Field(..., description="이메일로 보낸 인증 코드 6자리")

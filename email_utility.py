from fastapi_mail import FastMail, MessageSchema, MessageType

async def send_reset_email(fm: FastMail, user_email: str, verification_code: str, expires_minutes: int = 60):
    """
    비밀번호 재설정용 인증 코드 이메일 발송
    :param fm:
    :param user_email: 수신자 이메일
    :param verification_code: 발송할 6자리 코드
    :param expires_minutes: 코드 유효기간(분)
    """
    subject = "비밀번호 재설정 인증 코드 안내"
    body = f"""
    <html>
      <body>
        <h2>비밀번호 재설정 요청</h2>
        <p>회원님의 인증 코드는 <strong>{verification_code}</strong> 입니다.</p>
        <p>이 코드는 발송 시점으로부터 <strong>{expires_minutes}분</strong>간 유효합니다.</p>
        <hr/>
        <p>이 요청을 직접 하지 않으셨다면, 안전을 위해 비밀번호를 변경해주세요.</p>
      </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype=MessageType.html
    )
    await fm.send_message(message)

async def send_signup_verification_email(fm: FastMail, user_email: str, verification_code: str, expires_minutes: int = 60):
    subject = "이메일 주소 인증 코드 안내"
    body = f"""
        <html>
          <body>
            <h2>이메일 주소 인증</h2>
            <p><strong>{verification_code}</strong>를 입력해주세요.</p>
            <p>이 코드는 발송 시점으로부터 <strong>{expires_minutes}분</strong>간 유효합니다.</p>
            <hr/>
            <p>이 요청을 직접 하지 않으셨다면, 이 메일을 무시하셔도 됩니다.</p>
          </body>
        </html>
        """

    message = MessageSchema(
        subject=subject,
        recipients=[user_email],
        body=body,
        subtype=MessageType.html
    )
    await fm.send_message(message)

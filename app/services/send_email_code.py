import smtplib
from email.mime.text import MIMEText
from email.header import Header
from app.core.config import settings
from app.services.verification_code import VerificationCodeService


# 发送邮件验证码
def send_email_code(email: str, code: str):
    subject = "欢迎使用Saleor"
    content = f"验证码：{code}，过期时间为60s，转给他人将导致个人信息泄露，如非本人操作请忽略。"
    message = MIMEText(content, "plain", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = settings.smtp_sender
    message["To"] = email

    with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=10
    ) as server:

        # 是否启用 TLS 加密
        if settings.smtp_use_tls:
            server.starttls()

        # 是否需要 SMTP 登录认证
        if settings.smtp_user and settings.smtp_password:
            server.login(
                settings.smtp_user,
                settings.smtp_password
            )

        server.sendmail(
            settings.smtp_sender,
            [email],
            message.as_string()
        )

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from authx import AuthX, AuthXConfig

from app.core.config import settings
from app.models.models import User
from app.database import AsyncSessionLocal
from sqlalchemy.future import select
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


config = AuthXConfig(
    JWT_SECRET_KEY = settings.JWT_SECRET_KEY,
    JWT_ACCESS_COOKIE_NAME = "access_token",
    JWT_TOKEN_LOCATION = ["cookies"],
    JWT_ALGORITHM = settings.JWT_ALGORITHM,
)

JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM

security = AuthX(config=config)


async def authenticate_user(username: str, password: str) -> User | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user


def send_email_with_code(recipient: str, code: str) -> None:
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_SENDER
    msg['To'] = recipient
    msg['Subject'] = 'Your Password Reset Code'

    body = f'Your password reset code is: {code}\nIt is valid for 10 minutes.'
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
        server.send_message(msg)
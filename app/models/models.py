from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    reset_code = Column(String, nullable=True)  # 4-значный код
    reset_code_expiration = Column(DateTime, nullable=True)

class Firewall(Base):
    __tablename__ = "firewalls"

    uid = Column(Integer, primary_key=True, index=True)
    ip = Column(String(100), unique=True, index=True)
    port = Column(Integer, nullable=True)
    admin = Column(String(100), nullable=True)
    hash_password = Column(String, nullable=True)
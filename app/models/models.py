from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    reset_code = Column(String, nullable=True)
    reset_code_expiration = Column(DateTime, nullable=True)

    devicelog = relationship("DeviceLog", back_populates="user")


class ISGDevice(Base):
    __tablename__ = "isgdevice"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)
    ip_address = Column(String, unique=True, nullable=False)
    port = Column(Integer, nullable=False)
    admin_username = Column(String(100), nullable=False)
    admin_password = Column(String, nullable=False)


class DeviceLog(Base):
    __tablename__ = "devicelog"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    object_type = Column(String, nullable=False)
    object_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    details = Column(JSON, nullable=False)

    @property
    def username(self):
        return self.user.username if self.user else None

    user = relationship("User", back_populates="devicelog")

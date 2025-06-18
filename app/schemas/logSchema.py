from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceLogBase(BaseModel):
    action: str
    object_type: str
    object_id: int
    details: dict = None
    model_config = ConfigDict(from_attributes=True)

class DeviceLogCreate(DeviceLogBase):
    pass

class DeviceLog(DeviceLogBase):
    id: int
    user_id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class LogWithUser(DeviceLog):
    username: str
    model_config = ConfigDict(from_attributes=True)



from pydantic import BaseModel, ConfigDict


class ISGDeviceBase(BaseModel):
    uid: str
    ip_address: str
    port: int
    admin_username: str
    admin_password: str

    model_config = ConfigDict(from_attributes=True)


class ISGDeviceCreate(ISGDeviceBase):
    pass


class ISGDevice(ISGDeviceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Alert(BaseModel):
    timestamp: datetime
    event_type: str
    src_ip: str
    src_port: Optional[int]
    dest_ip: str
    dest_port: Optional[int]
    proto: str
    alert_signature: Optional[str]
    alert_severity: Optional[int]
    payload: Optional[str]
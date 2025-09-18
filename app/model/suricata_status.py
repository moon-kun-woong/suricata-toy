from pydantic import BaseModel
from typing import Optional

class SuricataStatus(BaseModel):
    is_running: bool
    pid: Optional[int]
    uptime: Optional[str]
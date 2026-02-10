from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.attendance import AttendanceStatus

class AttendanceBase(BaseModel):
    class_name: str
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: Optional[str] = None

class AttendanceCheckIn(AttendanceBase):
    user_id: int

class AttendanceMarkByTeacher(BaseModel):
    user_id: int
    class_name: str
    status: AttendanceStatus
    notes: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    id: int
    user_id: int
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    marked_by: Optional[int] = None
    
    class Config:
        from_attributes = True

class AttendanceWithUser(AttendanceResponse):
    username: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True
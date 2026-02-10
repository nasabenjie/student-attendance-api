from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_name = Column(String, nullable=False)  
    status = Column(SQLEnum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=True)  
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="attendance_records")
    marker = relationship("User", foreign_keys=[marked_by])
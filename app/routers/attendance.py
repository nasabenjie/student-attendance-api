from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import func
from typing import List
from datetime import datetime, date

from app.database import get_db
from app.models.attendance import Attendance, AttendanceStatus
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCheckIn, 
    AttendanceMarkByTeacher,
    AttendanceResponse,
    AttendanceWithUser
)

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"]
)

@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(attendance: AttendanceCheckIn, db: Session = Depends(get_db)):
    """Student checks in for a class"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == attendance.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already checked in today for this class
    today = datetime.now().date()
    existing = db.query(Attendance).filter(
        Attendance.user_id == attendance.user_id,
        Attendance.class_name == attendance.class_name,
        func.date(Attendance.check_in_time) == today
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in for this class today"
        )
    
    # Create attendance record
    db_attendance = Attendance(
        user_id=attendance.user_id,
        class_name=attendance.class_name,
        status=attendance.status,
        notes=attendance.notes
    )
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

@router.post("/mark", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(
    attendance: AttendanceMarkByTeacher, 
    teacher_id: int = Query(..., description="ID of teacher marking attendance"),
    db: Session = Depends(get_db)
):
    """Teacher marks student attendance"""
    
    # Verify teacher exists and is a teacher
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher or not teacher.is_teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can mark attendance"
        )
    
    # Verify student exists
    student = db.query(User).filter(User.id == attendance.user_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Create attendance record
    db_attendance = Attendance(
        user_id=attendance.user_id,
        class_name=attendance.class_name,
        status=attendance.status,
        notes=attendance.notes,
        marked_by=teacher_id
    )
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

@router.get("/", response_model=List[AttendanceResponse])
def get_all_attendance(
    skip: int = 0, 
    limit: int = 100,
    class_name: Optional[str] = None,
    date_filter: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get all attendance records with optional filters"""
    
    query = db.query(Attendance)
    
    if class_name:
        query = query.filter(Attendance.class_name == class_name)
    
    if date_filter:
        query = query.filter(func.date(Attendance.check_in_time) == date_filter)
    
    attendance = query.offset(skip).limit(limit).all()
    return attendance

@router.get("/user/{user_id}", response_model=List[AttendanceResponse])
def get_user_attendance(user_id: int, db: Session = Depends(get_db)):
    """Get attendance records for a specific user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    attendance = db.query(Attendance).filter(Attendance.user_id == user_id).all()
    return attendance

@router.get("/class/{class_name}/today", response_model=List[AttendanceWithUser])
def get_class_attendance_today(class_name: str, db: Session = Depends(get_db)):
    """Get today's attendance for a specific class"""
    
    today = datetime.now().date()
    
    attendance = db.query(Attendance, User).join(
        User, Attendance.user_id == User.id
    ).filter(
        Attendance.class_name == class_name,
        func.date(Attendance.check_in_time) == today
    ).all()
    
    result = []
    for att, user in attendance:
        result.append({
            "id": att.id,
            "user_id": att.user_id,
            "class_name": att.class_name,
            "status": att.status,
            "check_in_time": att.check_in_time,
            "check_out_time": att.check_out_time,
            "notes": att.notes,
            "marked_by": att.marked_by,
            "username": user.username,
            "full_name": user.full_name
        })
    
@router.get("/stats/user/{user_id}")
def get_user_attendance_stats(user_id: int, db: Session = Depends(get_db)):
    """Get attendance statistics for a user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all attendance records
    all_records = db.query(Attendance).filter(Attendance.user_id == user_id).all()
    
    if not all_records:
        return {
            "user_id": user_id,
            "username": user.username,
            "total_records": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
            "attendance_rate": 0
        }
    
    # Count by status
    present = len([r for r in all_records if r.status == AttendanceStatus.PRESENT])
    absent = len([r for r in all_records if r.status == AttendanceStatus.ABSENT])
    late = len([r for r in all_records if r.status == AttendanceStatus.LATE])
    excused = len([r for r in all_records if r.status == AttendanceStatus.EXCUSED])
    
    total = len(all_records)
    attendance_rate = round((present + late) / total * 100, 2) if total > 0 else 0
    
    return {
        "user_id": user_id,
        "username": user.username,
        "full_name": user.full_name,
        "total_records": total,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_rate": f"{attendance_rate}%"
    }


@router.get("/stats/class/{class_name}")
def get_class_attendance_stats(class_name: str, db: Session = Depends(get_db)):
    """Get attendance statistics for a class"""
    
    all_records = db.query(Attendance).filter(
        Attendance.class_name == class_name
    ).all()
    
    if not all_records:
        return {
            "class_name": class_name,
            "total_records": 0,
            "unique_students": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0
        }
    
    present = len([r for r in all_records if r.status == AttendanceStatus.PRESENT])
    absent = len([r for r in all_records if r.status == AttendanceStatus.ABSENT])
    late = len([r for r in all_records if r.status == AttendanceStatus.LATE])
    excused = len([r for r in all_records if r.status == AttendanceStatus.EXCUSED])
    
    unique_students = len(set([r.user_id for r in all_records]))
    
    return {
        "class_name": class_name,
        "total_records": len(all_records),
        "unique_students": unique_students,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused
    }
    
    return result
from app.schemas.user import UserCreate, UserResponse, UserBase
from app.schemas.attendance import (
    AttendanceCheckIn, 
    AttendanceMarkByTeacher, 
    AttendanceResponse,
    AttendanceWithUser
)
from app.schemas.auth import Token, LoginRequest, LoginResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users_router
from app.routers.attendance import router as attendance_router
from app.routers.auth import router as auth_router

app = FastAPI(
    title="Student Attendance API",
    description="API for managing student attendance and schedules",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(attendance_router)

@app.get("/")
def read_root():
    return {
        "message": "Student Attendance API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    try:
        from app.database import engine, Base
        from app.models import User, Attendance
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Database error: {e}")
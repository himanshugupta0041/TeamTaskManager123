from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import auth, projects, tasks

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Task Manager API",
    description="A full-featured task management system with MySQL database",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://frontend-team-manager.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)

@app.get("/")
def root():
    return {
        "message": "Team Task Manager API is running",
        "database": "MySQL",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "projects": "/api/projects",
            "tasks": "/api/tasks",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "MySQL connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

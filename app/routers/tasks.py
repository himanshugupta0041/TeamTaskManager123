from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models.user import User
from ..models.project import Project, ProjectMember
from ..models.task import Task, TaskStatus
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse
from ..dependencies.auth import get_current_active_user
from ..dependencies.permissions import require_project_access

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check project access
    require_project_access(task_data.project_id, current_user, db)
    
    # Check if assigned user exists
    assigned_user = db.query(User).filter(User.id == task_data.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="Assigned user not found")
    
    db_task = Task(
        **task_data.dict(),
        created_by=current_user.id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    assigned_to_me: Optional[bool] = Query(False, description="Get tasks assigned to me"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    
    # Filter by project
    if project_id:
        require_project_access(project_id, current_user, db)
        query = query.filter(Task.project_id == project_id)
    elif not current_user.role == "admin":
        # Get tasks from user's projects
        user_projects = db.query(ProjectMember.project_id).filter(ProjectMember.user_id == current_user.id)
        owned_projects = db.query(Project.id).filter(Project.owner_id == current_user.id)
        query = query.filter(
            (Task.project_id.in_(user_projects)) |
            (Task.project_id.in_(owned_projects))
        )
    
    # Filter by status
    if status:
        query = query.filter(Task.status == status)
    
    # Filter assigned to me
    if assigned_to_me:
        query = query.filter(Task.assigned_to == current_user.id)
    
    tasks = query.all()
    
    # Update overdue tasks
    today = date.today()
    for task in tasks:
        if task.due_date < today and task.status not in [TaskStatus.COMPLETED, TaskStatus.OVERDUE]:
            task.status = TaskStatus.OVERDUE
            db.commit()
    
    return tasks

@router.get("/dashboard")
def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get tasks assigned to user
    user_tasks = db.query(Task).filter(Task.assigned_to == current_user.id)
    
    # Update overdue tasks
    today = date.today()
    for task in user_tasks.all():
        if task.due_date < today and task.status not in [TaskStatus.COMPLETED, TaskStatus.OVERDUE]:
            task.status = TaskStatus.OVERDUE
            db.commit()
    
    total_tasks = user_tasks.count()
    pending_tasks = user_tasks.filter(Task.status == TaskStatus.PENDING).count()
    in_progress = user_tasks.filter(Task.status == TaskStatus.IN_PROGRESS).count()
    completed = user_tasks.filter(Task.status == TaskStatus.COMPLETED).count()
    overdue = user_tasks.filter(Task.status == TaskStatus.OVERDUE).count()
    
    # Get recent tasks
    recent_tasks = user_tasks.order_by(Task.created_at.desc()).limit(10).all()
    
    # Get project statistics
    user_projects = db.query(Project).filter(
        (Project.owner_id == current_user.id) |
        (Project.id.in_(
            db.query(ProjectMember.project_id).filter(ProjectMember.user_id == current_user.id)
        ))
    ).count()
    
    return {
        "stats": {
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "in_progress": in_progress,
            "completed_tasks": completed,
            "overdue_tasks": overdue
        },
        "recent_tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date
            } for t in recent_tasks
        ],
        "project_stats": {
            "total_projects": user_projects
        }
    }

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions (admin, project owner, task creator, or assignee)
    project = db.query(Project).filter(Project.id == task.project_id).first()
    has_access = (
        current_user.role == "admin" or
        (project and project.owner_id == current_user.id) or
        task.created_by == current_user.id or
        task.assigned_to == current_user.id
    )
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    for key, value in task_update.dict(exclude_unset=True).items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check permissions (admin or project owner)
    project = db.query(Project).filter(Project.id == task.project_id).first()
    has_access = (
        current_user.role == "admin" or
        (project and project.owner_id == current_user.id) or
        task.created_by == current_user.id
    )
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}
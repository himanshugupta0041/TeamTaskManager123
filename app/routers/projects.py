from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.project import Project, ProjectMember
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from ..dependencies.auth import get_current_active_user
from ..dependencies.permissions import require_project_access

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_project = Project(
        **project_data.dict(),
        owner_id=current_user.id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Add owner as a member
    project_member = ProjectMember(
        project_id=db_project.id,
        user_id=current_user.id
    )
    db.add(project_member)
    db.commit()
    
    return db_project

@router.get("/", response_model=List[ProjectResponse])
def get_user_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "admin":
        projects = db.query(Project).all()
    else:
        # Get projects where user is owner or member
        projects = db.query(Project).filter(
            (Project.owner_id == current_user.id) |
            (Project.id.in_(
                db.query(ProjectMember.project_id).filter(ProjectMember.user_id == current_user.id)
            ))
        ).all()
    
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    require_project_access(project_id, current_user, db)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions (admin or owner)
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    for key, value in project_update.dict(exclude_unset=True).items():
        setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions (admin or owner)
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}

@router.post("/{project_id}/members/{user_id}")
def add_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions
    if current_user.role != "admin" and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already member
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already in project")
    
    project_member = ProjectMember(project_id=project_id, user_id=user_id)
    db.add(project_member)
    db.commit()
    
    return {"message": "Member added successfully"}
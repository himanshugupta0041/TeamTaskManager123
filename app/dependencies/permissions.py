from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..models.user import User
from ..models.project import Project, ProjectMember

def require_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def require_project_access(project_id: int, current_user: User, db: Session):
    """
    Check if user has access to the project
    Access granted if: Admin, Project Owner, or Project Member
    """
    # Admin has access to all projects
    if current_user.role == "admin":
        return True
    
    # Check if project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Project owner has access
    if project.owner_id == current_user.id:
        return True
    
    # Check if user is a project member
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    return True
# init_db.py
from app.database import engine, Base
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task import Task
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # Create default admin user
        from sqlalchemy.orm import Session
        from app.utils.auth_utils import get_password_hash
        
        session = Session(engine)
        admin = session.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin_user = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("Admin@123"),
                full_name="System Admin",
                role="admin"
            )
            session.add(admin_user)
            session.commit()
            logger.info("Default admin user created! Email: admin@example.com, Password: Admin@123")
        
        session.close()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_database()
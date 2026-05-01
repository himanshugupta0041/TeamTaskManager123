from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # ensure string + safe length
    plain_password = str(plain_password)[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # ensure string + safe length
    password = str(password)[:72]
    return pwd_context.hash(password)

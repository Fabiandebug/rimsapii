
from pydantic.types import Json
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON
from ..base.models import Base
from ..permission.models import Role 
from ..utils.db_connection import get_db


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(100))
    email = Column(String(100), nullable=False)
    username = Column(String(50), nullable=True)
    active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    photo = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    deleted = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    verification_code = Column(String(100), nullable=True)
    principals = relationship("Principals", backref=backref("users", uselist=False))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    uuid = Column(String(100), nullable=True)

    @property 
    def role(self):
        _role = {}
        key = 100
        db = get_db()
        for principal in self.principals:
            if principal.value.split(":")[0].lower() == "role":
                code = principal.value.split(":")[1].lower()
                role = db.query(Role).filter(Role.code == code).first()
                if role.key < key: 
                    _role = {"code": code, "name": role.name, "key": role.key} 
                key = role.key 
        return _role 

    @property
    def roles(self):
        _roles = []
        db = get_db()
        for principal in self.principals:
            if principal.value.split(":")[0].lower() == "role":
                code = principal.value.split(":")[1].lower()
                role = db.query(Role).filter(Role.code == code).first()
                _roles.append({"code": code, "name": role.name, "key": role.key})
        return _roles
    
    def get_roles(self):
        _roles = []
        for principal in self.principals:
            if principal.value.split(":")[0].lower() == "role":
                code = principal.value.split(":")[1].lower()
                _roles.append(code)
        return _roles

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"

    def get_principals(self):
        _principals = [f"user:{self.id}"]
        for principal in self.principals:
            _principals.append(principal.value)
        
        return _principals

    @staticmethod
    def get_user_by_email(db: Session, email):
        user = db.query(User).filter(User.email == email).first()
        return user 
    
    @staticmethod
    def get_user_by_id(db: Session, id: int):
        user = db.query(User).filter(User.id == id).first()
        return user

    @staticmethod
    def get_user_by_verification_code(db: Session, code: str):
        user = db.query(User).filter(User.verification_code == code).first()
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username):
        user = db.query(User).filter(User.username == username).first()
        return user 
    
    @staticmethod
    def get_user_using_uuid(db: Session, uuid):
        user = db.query(User).filter(User.uuid == uuid).first()
        return user


class Principals(Base):
    __tablename__ = "principals"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
  

    def __str__(self) -> str:
        return self.value 
        

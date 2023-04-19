
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import func

from ..base.models import Base 


class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    key = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __str__(self) -> str:
        return self.code 
    
    @staticmethod
    def get_role_by_id(db: Session, id: int):
        return db.query(Role).filter(Role.id == id).first()
    
    @staticmethod
    def get_role_by_code(db: Session, code: str):
        return db.query(Role).filter(Role.code == code).first()


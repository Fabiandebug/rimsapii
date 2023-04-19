from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm.session import Session

from ..base.models import Base


class Institution(Base):
    __tablename__ = "institution"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(50), nullable=True)
    logo = Column(String(255), nullable=True)
    phone = Column(String(25), nullable=True)
    country = Column(String(50), nullable=True)
    address = Column(String(150), nullable=True)
    city = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    zipcode = Column(String(15), nullable=True)
    postalcode = Column(String(15), nullable=True)
    facebook_url = Column(String(150), nullable=True)
    twitter_url = Column(String(150), nullable=True)
    employee_count = Column(String(25), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    @staticmethod
    def get_institution(db: Session):
        institution = db.query(Institution).first()
        return institution

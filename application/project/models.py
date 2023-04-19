
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON

from ..base.models import Base 
from ..session.models import User 


class Progress:
    EXTRACTING = 'extracting'
    EXTRACTED = 'extracted'
    PROCESSING = 'processing'
    LOADING = 'loading'
    FAILED = 'failed'
    READY = 'ready'
    CREATED = "created"


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(1000), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref=backref("datasets", uselist=False))
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", back_populates="project_datasets")
    source = Column(String(200), nullable=True)
    file = Column(String(600), nullable=True)
    filename = Column(String(100), nullable=True)
    uuid_filename = Column(String(50), nullable=True)
    photo = Column(String(400), nullable=True)
    format = Column(String(10), nullable=True)
    stagging_tablename = Column(String(30), nullable=True)
    stagging_recordcount = Column(Integer, default=0)
    prod_tablename = Column(String(30), nullable=True)
    prod_recordcount = Column(Integer, default=0)
    resource_file = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=True)
    extraction_duration = Column(DECIMAL(10, 4), nullable=True)
    processing_duration = Column(DECIMAL(10, 4), nullable=True)
    loading_duration = Column(DECIMAL, nullable=True)
    imported = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)
    locked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    columns = relationship("DatasetColumn", back_populates="dataset")

    progress = Progress()

    @property 
    def fields(self):
        return len(self.columns)

    def get_column_name_list(self):
        cols = [c.name for c in self.columns]
        return cols
    
    def get_column_name_dict(self):
        result = {}
        for col in self.columns:
            result[col.name] = col.datatype
        return result 

    def get_name_as_key_column_dict(self):
        result = {}
        for col in self.columns:
            result[col.name] = {"name": col.name, "display_name": col.display_name, "datatype": col.datatype}
        return result 
    
    @staticmethod
    def get_dataset_by_id(db: Session, dataset_id):
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()


class DatasetColumn(Base):
    __tablename__ = "datasetcolumns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    datatype = Column(String(50), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    dataset = relationship("Dataset", back_populates="columns")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @staticmethod
    def get_column_by_id(db: Session, id:int):
        column = db.query(DatasetColumn).filter(DatasetColumn.id == id).first()
        return column 
    
    @staticmethod
    def get_column_by_name(db: Session, name:str):
        column = db.query(DatasetColumn).filter(DatasetColumn.name == name).first()
        return column 


class Tags(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, unique=True)
    projects = relationship("Project", secondary="projecttags", back_populates="tags")

    def __str__(self) -> str:
        return self.name


class Logs(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref=backref("user_projects", uselist=False))
    description = Column(String(1000))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    due_date = Column(DateTime, nullable=True)
    tags = relationship("Tags", secondary="projecttags", back_populates="projects")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref=backref("projects", uselist=False))
    status = Column(String(25), nullable=True)
    project_datasets = relationship("Dataset", back_populates="project")
    logs = relationship("Logs", backref=backref("projects", uselist=False))
    members = relationship("Members", backref=backref("project", uselist=False))
    banner_photo = Column(String(400), nullable=True)
    profile_photo = Column(String(400), nullable=True)
    data_package = Column(String(1000), nullable=True)
    archived = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    @property
    def datasets(self):
        return [ds for ds in self.project_datasets if ds.deleted == False]

    @property
    def project_tags(self):
        return [tag.name for tag in self.tags]

    @property 
    def project_members(self):
        return [member.user_id for member in self.members]

    @staticmethod 
    def get_project_by_id(db: Session, id: int):
        return db.query(Project).filter(Project.deleted == False).filter(Project.id == id).first()


class ProjectTags(Base):
    __tablename__ = "projecttags"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))

UniqueConstraint(ProjectTags.project_id, ProjectTags.tag_id)


class Members(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", foreign_keys=[user_id])
    project_id = Column(Integer, ForeignKey("projects.id"))
    addedby_id = Column(Integer, ForeignKey("users.id"))
    addedby = relationship("User", foreign_keys=[addedby_id])
    permission = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @staticmethod
    def get_user_project_id_list(db: Session, user_id:int):
        memberships = db.query(Members).filter(
            Members.user_id == user_id
        ).all()
        return [m.project_id for m in memberships if m.project.deleted == False]


class DownloadRequest(Base):
    __tablename__ = 'downloadrequests'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    format = Column(String(10))
    file = Column(String(1000), nullable=True)
    ready = Column(Boolean, default=False)
    exclude = Column(JSON, nullable=True)
    columns = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    dataset = relationship('Dataset', backref='reports')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', backref='reports')
    reportcolumns = relationship('ReportColumn', back_populates='report')
    deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @property
    def fields(self):
        return len(self.reportcolumns)

    @property
    def columns(self):
        return [col.column.name for col in self.reportcolumns]
    
    @property
    def column_dicts(self):
        col_list = []
        for col in self.reportcolumns:
            col_dict = {'name': col.column.name, "display_name": col.column.display_name, 'datatype': col.column.datatype}
            col_list.append(col_dict)
        return col_list

    @staticmethod
    def get_report_by_id(db:Session, id:int): 
        report = db.query(Report).filter(Report.id == id, Report.deleted == False).first()
        return report 
    

class ReportColumn(Base):
    __tablename__ = 'reportcolumns'

    id = Column(Integer, primary_key=True)
    column_id = Column(Integer, ForeignKey('datasetcolumns.id'))
    column = relationship('DatasetColumn', backref='reportcolumns')
    report_id = Column(Integer, ForeignKey('reports.id'))
    report = relationship('Report', back_populates='reportcolumns')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from src.db.db import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid1)
    username = Column(String(125), nullable=False, unique=True)
    hashed_password = Column(String(125), nullable=False)
    files = relationship('File', backref='user', cascade='save-update, merge, delete')
    created_at = Column(DateTime, index=True, default=datetime.utcnow)


class File(Base):
    __tablename__ = 'files'
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid1)
    user_id = Column(UUIDType(binary=False), ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    path = Column(String, nullable=False, unique=True)
    size = Column(Integer, nullable=False)
    is_downloadable = Column(Boolean, default=False)


class Directory(Base):
    __tablename__ = 'directories'
    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid1)
    path = Column(String, nullable=False, unique=True)


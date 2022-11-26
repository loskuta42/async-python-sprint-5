from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.db.db import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False, unique=True)
    files = relationship('File', backref='user', cascade='all, delete')
    created_at = Column(DateTime, index=True, default=datetime.utcnow)


class File(Base):
    __tablename__ = 'files'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    path = Column(String, nullable=False, unique=True)
    size = Column(Integer, nullable=False)
    is_downloadable = Column(Boolean, default=False)


class Directory(Base):
    __tablename__ = 'directories'
    id = Column(String, primary_key=True)
    path = Column(String, nullable=False, unique=True)


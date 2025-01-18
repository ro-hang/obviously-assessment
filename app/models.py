# app/models.py
from sqlalchemy import Column, Integer, String
from .db import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    published_date = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    genre = Column(String, nullable=True)

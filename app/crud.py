# app/crud.py
from sqlalchemy.orm import Session
from .models import Book
from .schemas import BookCreate, BookUpdate

def create_book(db: Session, book_in: BookCreate) -> Book:
    db_book = Book(**book_in.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_books(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Book).offset(skip).limit(limit).all()

def get_book_by_id(db: Session, book_id: int):
    return db.query(Book).filter(Book.id == book_id).first()

def update_book(db: Session, db_book: Book, updates: BookUpdate):
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, db_book: Book):
    db.delete(db_book)
    db.commit()

# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio
import json
from urllib.parse import urlencode

from .db import SessionLocal, engine, Base
from .models import Book
from . import crud
from .schemas import (
    BookCreate,
    BookRead,
    BookUpdate,
    TokenSchema,
    PaginatedBooks
)
from .auth import authenticate_user, create_access_token, get_current_user
from .event_manager import event_queue

# Create DB tables if they don't already exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Books CRUD API",
    description=(
        "A FastAPI application that provides a JWT-protected CRUD interface for managing books, plus a real-time SSE endpoint."
        "Use `/login` to obtain a token, or just hit authorize with the username and password to use the secured endpoints."
    ),
    version="1.0.0",
    contact={
        "url": "https://github.com/ro-hang/obviously-assessment",
    }
)

def get_db():
    """
    Dependency that yields a DB session.
    Closes session automatically after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# LOGIN (OAuth2 "Password" Flow)
# -----------------------------
@app.post(
    "/login",
    response_model=TokenSchema,
    tags=["authentication"],
    summary="Obtain JWT Token",
    description=(
        "Use this endpoint to authenticate with the username & password to obtain a JWT token. This token is required to access all other CRUD endpoints."
    ),
    responses={
        401: {"description": "Invalid username or password"},
    }
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    #using this OAuth2PasswordRequestForm just to do the username and password validation
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post(
    "/books/",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
    tags=["books"],
    summary="Create a New Book",
    description="Add a new book record to the database."
)
async def create_new_book(
    book_in: BookCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    new_book = crud.create_book(db, book_in)
    event_data = {
        "action": "created",
        "book_id": new_book.id,
        "title": new_book.title
    }
    await event_queue.put(event_data)
    return new_book


@app.get(
    "/books/",
    response_model=PaginatedBooks,
    tags=["books"],
    summary="List All Books (Paginated)",
    description="Retrieve a paginated list of all books in the database."
)
async def read_all_books(
    request: Request,
    skip: int = Query(
        0,
        description="Number of records to skip before selecting books.",
        ge=0
    ),
    limit: int = Query(
        10,
        description="Max number of books to return.",
        ge=1
    ),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieves books from the database with pagination support **and** next/prev links.

    Query Parameters:
    - skip: Records to skip (default=0).
    - limit: Maximum number of books to return (default=10).

    Returns:
    An object with:
    - data: list of Book objects
    - total_count: total number of books
    - next_url: link to the next page (or null if none)
    - prev_url: link to the previous page (or null if none)
    """
    # 1. Count total records
    total_count = db.query(Book).count()

    # 2. Retrieve this page of books
    books = crud.get_books(db, skip=skip, limit=limit)

    # 3. Calculate next_url if there's another page
    next_url = None
    if (skip + limit) < total_count:
        # e.g., /books/?skip=10&limit=10
        query_params = {"skip": skip + limit, "limit": limit}
        next_url = f"{request.url.path}?{urlencode(query_params)}"

    # 4. Calculate prev_url if skip > 0
    prev_url = None
    if skip > 0:
        new_skip = max(skip - limit, 0)
        query_params = {"skip": new_skip, "limit": limit}
        prev_url = f"{request.url.path}?{urlencode(query_params)}"

    # 5. Return the PaginatedBooks response
    return PaginatedBooks(
        data=books,
        total_count=total_count,
        next_url=next_url,
        prev_url=prev_url
    )


@app.get(
    "/books/{book_id}",
    response_model=BookRead,
    tags=["books"],
    summary="Get Book by ID",
    description="Retrieve details of a single book by its unique ID.",
    responses={
        404: {"description": "Book not found"}
    }
)
async def read_book_by_id(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    book = crud.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    event_data = {
        "action": "read",
        "book_id": book.id,
        "title": book.title
    }
    await event_queue.put(event_data)
    return book


@app.put(
    "/books/{book_id}",
    response_model=BookRead,
    tags=["books"],
    summary="Update Book by ID",
    description="Update any subset of fields for the specified book. Any fields not provided will remain unchanged.",
    responses={
        404: {"description": "Book not found"}
    }
)
async def update_book_by_id(
    book_id: int,
    updates: BookUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    book = crud.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    updated_book = crud.update_book(db, book, updates)
    event_data = {
        "action": "updated",
        "book_id": updated_book.id,
        "title": updated_book.title
    }
    await event_queue.put(event_data)
    return updated_book


@app.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["books"],
    summary="Delete Book by ID",
    description="Permanently remove a book from the database.",
    responses={
        404: {"description": "Book not found"},
        204: {"description": "Book successfully deleted (no content returned)."}
    }
)
async def delete_book_by_id(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    book = crud.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    crud.delete_book(db, book)
    event_data = {
        "action": "deleted",
        "book_id": book_id
    }
    await event_queue.put(event_data)
    return


@app.get(
    "/sse",
    response_class=StreamingResponse,
    tags=["SSE"],
    summary="Real-Time Updates (SSE)",
    description=(
        "Subscribes to a stream of Server-Sent Events. Whenever a book is created, read, updated, or deleted, the server broadcasts a JSON message. "
        "**Requires** Bearer token to connect."
    )
)
async def sse_endpoint(current_user: str = Depends(get_current_user)):

    async def event_generator():
        while True:
            event_data = await event_queue.get()
            message_json = json.dumps(event_data)
            # SSE format: data: <json>\n\n
            yield f"data: {message_json}\n\n"
            event_queue.task_done()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch any unhandled exceptions and return a 500 response.
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred on the server."}
    )

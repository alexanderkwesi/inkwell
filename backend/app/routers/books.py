from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Book, Chapter, UploadedFile
from app.schemas import (
    BookCreate,
    BookResponse,
    BookDetailsResponse,
    BookListResponse,
)
from app.security import get_current_user
from app.config import PLAN_LIMITS
from app.services.claude import generate_book_via_claude

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("", response_model=BookListResponse)
def list_books(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.user_id == current_user.id).order_by(Book.created_at.desc()).all()
    return {"books": books}


@router.post("/generate", response_model=BookDetailsResponse, status_code=status.HTTP_201_CREATED)
async def generate_book(
    data: BookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check plan limits
    limit = PLAN_LIMITS.get(current_user.plan, 4)
    if current_user.books_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Book limit reached ({current_user.books_used}/{limit}) for your {current_user.plan} plan. Please upgrade."
        )

    # Compile files context (any file uploaded by user that isn't yet attached to a book)
    unattached_files = db.query(UploadedFile).filter(
        UploadedFile.user_id == current_user.id,
        UploadedFile.book_id == None
    ).all()
    
    files_context = ""
    if unattached_files:
        files_context = ", ".join([f.filename for f in unattached_files])

    # Call Claude API Service
    book_outline = await generate_book_via_claude(data.prompt, files_context)

    # Persist outline and chapters to SQLite Database
    db.begin_nested() if db.in_nested_transaction() else None
    try:
        new_book = Book(
            user_id=current_user.id,
            title=book_outline["title"][:300],
            synopsis=book_outline.get("synopsis", ""),
            prompt=data.prompt,
            chapter_count=len(book_outline["chapters"]),
            status="complete"
        )
        db.add(new_book)
        db.flush()  # gets new_book.id

        chapters_list = []
        for ch_data in book_outline["chapters"]:
            chapter = Chapter(
                book_id=new_book.id,
                chapter_number=int(ch_data["number"]),
                title=ch_data["title"][:300],
                content=ch_data["content"],
                image_description=ch_data.get("imageDescription", "")
            )
            db.add(chapter)
            chapters_list.append(chapter)

        # Link files to this book
        for f in unattached_files:
            f.book_id = new_book.id

        # Increment user usage count
        current_user.books_used += 1
        current_user.updated_at = datetime.utcnow()

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save generated book data: {e}"
        )

    # Return constructed book with chapters
    return {
        "id": new_book.id,
        "title": new_book.title,
        "synopsis": new_book.synopsis,
        "chapter_count": new_book.chapter_count,
        "status": new_book.status,
        "created_at": new_book.created_at,
        "updated_at": new_book.updated_at,
        "prompt": new_book.prompt,
        "chapters": chapters_list
    }


@router.get("/{book_id}", response_model=BookDetailsResponse)
def get_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id, Book.user_id == current_user.id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    
    # Eagerly load chapters
    chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
    
    return {
        "id": book.id,
        "title": book.title,
        "synopsis": book.synopsis,
        "chapter_count": book.chapter_count,
        "status": book.status,
        "created_at": book.created_at,
        "updated_at": book.updated_at,
        "prompt": book.prompt,
        "chapters": chapters
    }


@router.delete("/{book_id}")
def delete_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id, Book.user_id == current_user.id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    db.delete(book)
    
    # Decrement books_used count, ensure >= 0
    current_user.books_used = max(current_user.books_used - 1, 0)
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Book deleted."}


@router.post("/{book_id}/export")
def export_book(
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # mPDF placeholder replication
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="PDF export is available on Pro and Elite plans. Coming soon."
    )

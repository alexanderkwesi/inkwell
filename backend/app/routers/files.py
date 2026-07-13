import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UploadedFile
from app.schemas import FileResponse, FileListResponse
from app.security import get_current_user
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/files", tags=["Files"])

@router.get("", response_model=FileListResponse)
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files = db.query(UploadedFile).filter(
        UploadedFile.user_id == current_user.id
    ).order_by(UploadedFile.created_at.desc()).all()
    return {"files": files}


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    book_id: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 20 MB limit
    max_bytes = 20 * 1024 * 1024
    
    # Read partial content to verify size, or read all
    content = await file.read()
    file_size = len(content)
    if file_size > max_bytes:
        raise HTTPException(status_code=400, detail="File too large. Maximum is 20 MB.")

    mime_type = file.content_type
    allowed_types = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp"
    ]
    if mime_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Accepted: PDF, TXT, MD, DOCX, JPEG, PNG, GIF, WEBP."
        )

    file_type = "image" if mime_type.startswith("image/") else "document"
    
    # Secure storage path
    user_upload_dir = os.path.join(UPLOAD_DIR, current_user.id)
    if not os.path.exists(user_upload_dir):
        os.makedirs(user_upload_dir, mode=0o750)

    # Unique storage name
    ext = os.path.splitext(file.filename)[1].lower()
    unique_name = f"{uuid.uuid4()}{ext}"
    storage_key = f"uploads/{current_user.id}/{unique_name}"
    local_path = os.path.join(user_upload_dir, unique_name)

    # Save to disk
    try:
        with open(local_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file on disk: {e}")

    # Register in DB
    db_file = UploadedFile(
        user_id=current_user.id,
        book_id=book_id if book_id else None,
        filename=file.filename,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size_bytes=file_size,
        file_type=file_type,
        created_at=datetime.utcnow()
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")

    # Remove from storage
    # storage_key starts with "uploads/{user_id}/unique_name.ext"
    # UPLOAD_DIR is mapped to parent of C:\Users\user\.gemini\antigravity\scratch\inkwell-ai\backend\storage\uploads
    # Let's map it cleanly
    parts = record.storage_key.split("/")
    if len(parts) >= 3:
        unique_name = parts[-1]
        local_path = os.path.join(UPLOAD_DIR, current_user.id, unique_name)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass # Continue to delete DB row even if disk delete fails

    db.delete(record)
    db.commit()
    return {"message": "File deleted."}

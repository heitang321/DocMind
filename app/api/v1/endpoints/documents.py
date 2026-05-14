# app/api/v1/endpoints/documents.py
import os
import time
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, User, Document, Chunk
from app.core.security import get_current_user
from app.services.faiss_index import rebuild_user_index

router = APIRouter(prefix="/documents", tags=["文档管理"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """安全的分块函数，确保每次循环 start 都会前进"""
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        # 如果不是最后一块，尝试在空格处截断
        if end < text_len:
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # 计算下一个起始位置，确保至少前进1个字符
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start
    return chunks

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(('.txt', '.md')):
        raise HTTPException(status_code=400, detail="只支持 .txt 和 .md 文件")

    content = await file.read()
    safe_filename = f"{current_user.id}_{int(time.time())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(content)

    doc = Document(
        filename=safe_filename,
        original_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        user_id=current_user.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码不是UTF-8")

    chunks = chunk_text(text_content)
    for idx, chunk_content in enumerate(chunks):
        chunk = Chunk(
            document_id=doc.id,
            chunk_index=idx,
            content=chunk_content
        )
        db.add(chunk)
    await db.commit()
    print("开始重建索引...")   # 加这行
    # 异步重建索引（会使用传入的 db 会话，注意该会话在请求结束后会关闭，但函数内会读取数据库）
    await rebuild_user_index(current_user.id, db)
    print("索引重建完成")
    return {
        "id": doc.id,
        "filename": doc.original_name,
        "chunk_count": len(chunks),
        "message": "上传成功并已建立索引"
    }
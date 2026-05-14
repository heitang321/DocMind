# app/services/faiss_index.py
import os
import numpy as np
import faiss
import pickle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding import embedding_service
from app.models.database import Chunk, Document

INDEX_DIR = "faiss_indexes"
os.makedirs(INDEX_DIR, exist_ok=True)

def get_user_index_path(user_id: int) -> str:
    return os.path.join(INDEX_DIR, f"user_{user_id}.faiss")

def get_user_id_to_chunk_path(user_id: int) -> str:
    return os.path.join(INDEX_DIR, f"user_{user_id}_chunk_ids.pkl")

async def rebuild_user_index(user_id: int, db: AsyncSession):
    """从数据库 chunks 表重建用户的 FAISS 索引（异步版本）"""
    print(f"[rebuild_user_index] 开始处理 user_id={user_id}")
    try:
        # 查询该用户所有文档的所有分块
        stmt = select(Chunk).join(Document).where(Document.user_id == user_id)
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        print(f"[rebuild_user_index] 查询到 {len(chunks)} 个分块")

        if not chunks:
            # 没有分块，删除旧索引文件
            print("[rebuild_user_index] 无分块，删除旧索引文件")
            for path in [get_user_index_path(user_id), get_user_id_to_chunk_path(user_id)]:
                if os.path.exists(path):
                    os.remove(path)
            return

        texts = [chunk.content for chunk in chunks]
        print("[rebuild_user_index] 开始向量化...")
        vectors = embedding_service.encode(texts)          # 得到 (n, 384) 的 numpy 数组
        print(f"[rebuild_user_index] 向量化完成，向量形状: {vectors.shape}")
        
        print("[rebuild_user_index] 归一化并创建 FAISS 索引...")
        faiss.normalize_L2(vectors)                        # 归一化以便使用内积作为余弦相似度
        index = faiss.IndexFlatIP(embedding_service.dimension)
        index.add(vectors)
        print("[rebuild_user_index] 索引创建成功，保存文件...")

        # 保存 FAISS 索引
        faiss.write_index(index, get_user_index_path(user_id))

        # 保存 chunk_id 列表（顺序与索引中的向量顺序一致）
        chunk_ids = [chunk.id for chunk in chunks]
        with open(get_user_id_to_chunk_path(user_id), 'wb') as f:
            pickle.dump(chunk_ids, f)
        print("[rebuild_user_index] 索引和 chunk_ids 保存成功")
    except Exception as e:
        print(f"[rebuild_user_index] 出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise

def search_user_index(user_id: int, query: str, top_k: int = 5):
    """同步检索用户知识库中最相似的 top_k 个文本块，返回 (chunk_id, score) 列表"""
    index_path = get_user_index_path(user_id)
    id_path = get_user_id_to_chunk_path(user_id)
    if not os.path.exists(index_path) or not os.path.exists(id_path):
        return []

    index = faiss.read_index(index_path)
    with open(id_path, 'rb') as f:
        chunk_ids = pickle.load(f)

    query_vec = embedding_service.encode([query])
    faiss.normalize_L2(query_vec)
    scores, indices = index.search(query_vec, min(top_k, len(chunk_ids)))

    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx != -1:
            results.append((chunk_ids[idx], float(score)))
    return results
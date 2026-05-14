# app/api/v1/endpoints/qa.py
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from app.models.database import get_db, User, Chunk
from app.core.security import get_current_user
from app.services.faiss_index import search_user_index

# 加载 .env 环境变量
load_dotenv()

router = APIRouter(prefix="/qa", tags=["问答"])

# 请求和响应的数据模型
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5

class AnswerItem(BaseModel):
    chunk_id: int
    score: float
    content: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[AnswerItem]  # 新增 sources，用于展示答案来源
    usage: dict = {}  # 可选，记录 token 消耗

@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """基于用户知识库检索，并使用 LLM 生成最终答案"""
    # 1. 检索相似文本块
    results = search_user_index(current_user.id, req.question, top_k=req.top_k)
    if not results:
        # 无检索结果时，直接返回答案
        return QueryResponse(
            question=req.question,
            answer="抱歉，在您的知识库中没有找到与问题相关的资料，暂时无法回答。",
            sources=[]
        )
    
    # 2. 获取检索到的分块内容和 ID
    chunk_ids = [r[0] for r in results]
    stmt = select(Chunk).where(Chunk.id.in_(chunk_ids))
    result = await db.execute(stmt)
    chunks_map = {chunk.id: chunk for chunk in result.scalars()}
    
    # 准备上下文和来源列表
    contexts = []
    sources = []
    for chunk_id, score in results:
        chunk = chunks_map.get(chunk_id)
        if chunk:
            contexts.append(chunk.content)
            sources.append(AnswerItem(chunk_id=chunk_id, score=score, content=chunk.content[:200]))
    
    if not contexts:
        return QueryResponse(
            question=req.question,
            answer="未找到有效的资料，请尝试上传新的文档。",
            sources=[]
        )
    
    # 3. 构造发送给大模型的 Prompt
    context_str = "\n\n---\n\n".join(contexts)
    prompt = f"""你是一个专业的、基于知识库的问答助手。请严格依据以下提供的参考资料，回答用户的问题。
*   如果参考资料足以回答问题，请给出一个简洁、准确、使用中文的答案，并可以提及信息来源。
*   如果参考资料不足以回答问题（例如信息不完整或包含“无法回答”等提示），请直接回答：“根据现有资料无法回答该问题。”

### 参考资料：
{context_str}

### 用户的问题：
{req.question}

### 你的回答："""
    
    # 4. 调用大语言模型 API
    try:
        # 初始化 DeepSeek 客户端
        client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        
        # 发送请求
        response = client.chat.completions.create(
            model="deepseek-chat",  # 或者 "deepseek-v4-pro", "deepseek-v4-flash"
            messages=[
                {"role": "system", "content": "你是一个知识库问答助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 降低随机性，让回答更忠实于资料
            max_tokens=2000   # 限制回答长度
        )
        answer = response.choices[0].message.content
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
    except Exception as e:
        # 如果 LLM 调用失败，仍返回检索到的原始资料，确保服务可用
        answer = f"无法调用语言模型生成最终答案 (错误: {e})。以下是相关参考资料摘要：\n"
        answer += "\n".join([f"- {ctx[:200]}..." for ctx in contexts[:3]])
        usage = {}
    
    return QueryResponse(
        question=req.question,
        answer=answer,
        sources=sources,
        usage=usage
    )
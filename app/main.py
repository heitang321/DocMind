# app/main.py

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.v1.endpoints import auth, documents, qa
from app.models.database import engine, Base


# 应用生命周期：启动时自动创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


# 创建 FastAPI 应用
app = FastAPI(
    title="DocMind API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改成指定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")

# 确保静态目录存在
static_dir = "frontend"

if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# 根路径
@app.get("/")
async def root():

    index_path = os.path.join(static_dir, "index.html")

    # 如果前端页面存在，则返回前端
    if os.path.exists(index_path):
        return FileResponse(index_path)

    # 否则返回 API 状态
    return {"message": "DocMind API is running"}
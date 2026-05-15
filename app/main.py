# app/main.py
# FastAPI 应用入口

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, documents,qa
from app.models.database import Base, engine
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="DocMind API", version="1.0.0")

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 配置 CORS（允许前端跨域访问，后面会用到）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发时允许所有，生产需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")

# 确保静态文件目录存在
static_dir = "frontend"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件，路径 /static 对应 frontend 目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 可选：根路径返回 index.html
from fastapi.responses import FileResponse
@app.get("/")
async def get_index():
    return FileResponse(os.path.join(static_dir, "index.html"))
@app.get("/")
async def root():
    return {"message": "DocMind API is running"}
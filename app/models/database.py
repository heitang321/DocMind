# app/models/database.py
# 数据库引擎、会话工厂、基类配置

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

# 创建异步数据库引擎
# echo=True 会在控制台打印执行的 SQL 语句，便于调试
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,              # 开发时打印 SQL，生产环境可设为 False
    future=True,           # 使用 SQLAlchemy 2.0 风格
    pool_size=10,          # 连接池大小
    max_overflow=20        # 连接池溢出容量
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False   # 提交后不过期对象
)

# 声明基类，所有模型类都要继承它
class Base(DeclarativeBase):
    pass

# 依赖项：获取数据库会话（用于在路由函数中注入）
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ---------- 模型定义 ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系（将在 Document 定义后自动解析）
    documents = relationship("Document", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)   # 服务器存储路径
    file_size = Column(Integer)                       # 字节
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    user = relationship("User", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)    # 第几个分块
    content = Column(Text, nullable=False)            # 分块文本内容
    embedding = Column(Text, nullable=True)           # 存储向量的 JSON 字符串（暂未使用）

    document = relationship("Document", back_populates="chunks")
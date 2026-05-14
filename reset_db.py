# reset_db.py
import asyncio
import sys

# 针对 Windows 设置事件循环策略
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.models.database import engine, Base
from app.models.database import User, Document, Chunk  # 导入所有模型

async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)   # 删除所有表
        await conn.run_sync(Base.metadata.create_all) # 重新创建
        print("数据库已重置并重新创建所有表")

if __name__ == "__main__":
    asyncio.run(reset())
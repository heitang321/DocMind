# init_db.py - 初始化数据库表（开发用）
import asyncio
from app.models.database import engine, Base
from app.models.database import User  # 导入模型，确保 Base 注册了它

async def init():
    async with engine.begin() as conn:
        # 删除所有表（谨慎！生产不要用）
        # await conn.run_sync(Base.metadata.drop_all)
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表创建完成")

if __name__ == "__main__":
    asyncio.run(init())
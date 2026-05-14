# app/core/config.py
# 配置管理模块，使用 Pydantic Settings 从 .env 加载环境变量

from pydantic_settings import BaseSettings   # 配置基类
from pydantic import ConfigDict              # 配置模型的行为

class Settings(BaseSettings):
    """应用配置类"""
    # 数据库连接 URL，从环境变量 DATABASE_URL 读取
    DATABASE_URL: str
    
    # JWT 相关配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"                 # 默认值，可在 .env 中覆盖
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200 # 默认30天
    
    # Pydantic 配置：指定 .env 文件的路径和编码
    model_config = ConfigDict(
        env_file=".env",          # 从根目录的 .env 文件读取
        env_file_encoding="utf-8",# 文件编码
        extra="ignore"            # 忽略额外的环境变量
    )

# 创建全局配置实例，供其他模块导入使用
settings = Settings()
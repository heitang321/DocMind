# test_config.py - 临时测试脚本
from app.core.config import settings

print("DATABASE_URL:", settings.DATABASE_URL)
print("SECRET_KEY[:10]:", settings.SECRET_KEY[:10])  # 只打印前10个字符保密
print("ALGORITHM:", settings.ALGORITHM)
print("ACCESS_TOKEN_EXPIRE_MINUTES:", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
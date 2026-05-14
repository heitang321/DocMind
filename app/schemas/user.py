# app/schemas/user.py
# 定义请求和响应的数据格式（Pydantic 模型）

from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    """共享字段"""
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """注册请求体"""
    password: str

class UserResponse(UserBase):
    """返回给客户端的用户信息（不包含密码）"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True  # 允许从 ORM 对象自动转换

class Token(BaseModel):
    """登录成功返回的 Token"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token 中携带的数据"""
    username: str | None = None
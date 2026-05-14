# app/api/v1/endpoints/auth.py
# 用户认证相关路由

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm

from app.models.database import get_db, User
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册（带调试输出）"""
    import traceback  # 放在这里便于调试
    try:
        # 检查用户名是否已存在
        stmt = select(User).where(User.username == user_data.username)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被注册"
            )
        
        # 检查邮箱是否已存在
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        existing_email = result.scalar_one_or_none()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建新用户（密码哈希后存储）
        hashed_pwd = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pwd
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)  # 刷新获取自增 id
        
        return new_user
    except Exception as e:
        # 打印完整错误堆栈到终端
        traceback.print_exc()
        # 重新抛出异常，让 FastAPI 返回 500
        raise e

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录，返回 JWT token（支持 OAuth2 表单）"""
    # 查询用户
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成 token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息（需要认证）"""
    return current_user
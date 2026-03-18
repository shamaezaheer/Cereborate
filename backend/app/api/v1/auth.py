import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.deps import get_current_user_id, get_db
from app.models.user import MemberRole, Tenant, TenantMembership, User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    TenantResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, tenant_id: str) -> tuple[str, int]:
    expiry_minutes = settings.jwt_expiry_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expiry_minutes * 60


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check slug uniqueness
    existing_tenant = await db.scalar(select(Tenant).where(Tenant.slug == data.tenant_slug))
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Tenant slug already taken")

    tenant = Tenant(
        name=data.tenant_name,
        slug=data.tenant_slug,
    )
    db.add(tenant)
    await db.flush()

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.flush()

    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role=MemberRole.owner,
        access_tier=10,
        invited_at=datetime.now(timezone.utc),
    )
    db.add(membership)
    await db.commit()
    await db.refresh(user)
    await db.refresh(tenant)

    token, expires_in = create_access_token(str(user.id), str(tenant.id))

    return RegisterResponse(
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant),
        token=TokenResponse(access_token=token, expires_in=expires_in),
    )


@router.post("/login", response_model=RegisterResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == user.id)
    )
    if not membership:
        raise HTTPException(status_code=400, detail="User has no tenant membership")

    tenant = await db.get(Tenant, membership.tenant_id)
    token, expires_in = create_access_token(str(user.id), str(membership.tenant_id))

    return RegisterResponse(
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant),
        token=TokenResponse(access_token=token, expires_in=expires_in),
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    membership = await db.scalar(
        select(TenantMembership).where(TenantMembership.user_id == user.id)
    )
    if not membership:
        raise HTTPException(status_code=400, detail="No membership found")

    tenant = await db.get(Tenant, membership.tenant_id)

    return MeResponse(
        user=UserResponse.model_validate(user),
        tenant=TenantResponse.model_validate(tenant),
        role=membership.role,
        access_tier=membership.access_tier,
    )

"""
CloudPulse Authentication Endpoints
"""
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from backend.app.models.models import User, Organization, OrganizationMember
from backend.app.schemas.schemas import UserCreate, UserLogin, UserOut, Token

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Registers a new administrator/engineer account with a dedicated organization."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 1. Create User
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name or user_in.email.split("@")[0],
        role="admin"
    )
    db.add(new_user)
    db.flush()

    # 2. Create Default Organization
    org_slug = f"org-{uuid.uuid4().hex[:8]}"
    org_name = user_in.organization_name or "CloudPulse Default Org"
    new_org = Organization(
        name=org_name,
        slug=org_slug,
        description=f"Primary infrastructure organization for {new_user.full_name}"
    )
    db.add(new_org)
    db.flush()

    # 3. Create Membership
    membership = OrganizationMember(
        user_id=new_user.id,
        organization_id=new_org.id,
        role="owner"
    )
    db.add(membership)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user.id, org_id=new_org.id, role="admin")
    refresh_token = create_refresh_token(new_user.id)

    user_out = UserOut(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        is_superuser=new_user.is_superuser,
        role=new_user.role,
        organization_id=new_org.id,
        created_at=new_user.created_at
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_out
    )


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    """Authenticates credentials and returns JWT access & refresh tokens."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated.")

    # Get user's primary organization
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    org_id = membership.organization_id if membership else ""

    access_token = create_access_token(user.id, org_id=org_id, role=user.role)
    refresh_token = create_refresh_token(user.id)

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
        organization_id=org_id,
        created_at=user.created_at
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_out
    )


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)) -> Any:
    """Generates a new access token from a valid refresh token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    org_id = membership.organization_id if membership else ""

    new_access_token = create_access_token(user.id, org_id=org_id, role=user.role)
    new_refresh_token = create_refresh_token(user.id)

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        role=user.role,
        organization_id=org_id,
        created_at=user.created_at
    )

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=user_out
    )


@router.post("/logout")
def logout() -> Any:
    """Client-side token disposal confirmation."""
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Any:
    """Retrieves authenticated user profile and tenant organization ID."""
    membership = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user.id).first()
    org_id = membership.organization_id if membership else None

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        role=current_user.role,
        organization_id=org_id,
        created_at=current_user.created_at
    )

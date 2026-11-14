"""
CloudPulse API Dependencies
FastAPI dependencies for JWT authentication, organization isolation, and Agent Token verification.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_token, hash_agent_token
from backend.app.database.session import get_db
from backend.app.models.models import User, Organization, OrganizationMember, Server, AgentCredential

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_exception
    return user


def get_current_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Organization:
    """Enforces multi-tenant data isolation by returning the user's active organization."""
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="User is not assigned to any organization.")

    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


def verify_agent_auth(
    x_agent_token: Optional[str] = Header(None, alias="X-Agent-Token"),
    x_server_id: Optional[str] = Header(None, alias="X-Server-ID"),
    db: Session = Depends(get_db)
) -> Server:
    """Authenticates the Python monitoring agent via server ID and hashed token."""
    if not x_agent_token or not x_server_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Agent-Token or X-Server-ID header."
        )

    server = db.query(Server).filter(Server.id == x_server_id, Server.is_active == True).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found or inactive.")

    cred = db.query(AgentCredential).filter(AgentCredential.server_id == server.id).first()
    if not cred or cred.is_revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agent credentials invalid or revoked.")

    expected_hash = hash_agent_token(x_agent_token)
    if cred.agent_token_hash != expected_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Agent Token.")

    return server

import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Enum, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from enum import Enum
import redis
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class UserRole(str, Enum):
    ADMIN = "admin"
    PREMIUM = "premium"
    STANDARD = "standard"
    READONLY = "readonly"
    TRIAL = "trial"

class APIKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    DISCOVER = "discover"
    ANALYZE = "analyze"
    SANDBOX = "sandbox"
    METRICS = "metrics"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(16))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.STANDARD)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Subscription information
    subscription_tier = Column(Enum(UserRole), default=UserRole.STANDARD)
    subscription_expires_at = Column(DateTime)
    api_quota = Column(Integer, default=1000)
    api_usage = Column(Integer, default=0)
    
    # Rate limiting
    rate_limit_requests_per_minute = Column(Integer, default=60)
    rate_limit_requests_per_hour = Column(Integer, default=1000)
    rate_limit_requests_per_day = Column(Integer, default=10000)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(32))
    key_hash = Column(String, nullable=False, unique=True, index=True)
    key_prefix = Column(String, nullable=False)  # First 8 characters for display
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    scopes = Column(Text, default=json.dumps([APIKeyScope.READ.value]))
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Rate limiting for this key
    rate_limit_requests_per_minute = Column(Integer, default=60)
    rate_limit_requests_per_hour = Column(Integer, default=1000)
    rate_limit_requests_per_day = Column(Integer, default=10000)
    
    # IP restrictions
    allowed_ips = Column(Text)  # JSON array of allowed IP addresses
    allowed_origins = Column(Text)  # JSON array of allowed origins
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    audit_logs = relationship("AuditLog", back_populates="api_key")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(32))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String, nullable=False, unique=True, index=True)
    refresh_token = Column(String, nullable=False, unique=True, index=True)
    ip_address = Column(String)
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: secrets.token_urlsafe(32))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True, index=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=False)
    resource_id = Column(String)
    details = Column(Text)  # JSON string with additional details
    ip_address = Column(String)
    user_agent = Column(Text)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    api_key = relationship("APIKey", back_populates="audit_logs")

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(String, primary_key=True, default="system")
    public_readonly_mode = Column(Boolean, default=False, index=True)
    allow_registration = Column(Boolean, default=True)
    default_user_role = Column(Enum(UserRole), default=UserRole.STANDARD)
    trial_period_days = Column(Integer, default=14)
    max_api_keys_per_user = Column(Integer, default=5)
    require_email_verification = Column(Boolean, default=True)
    password_min_length = Column(Integer, default=8)
    session_timeout_hours = Column(Integer, default=24)
    jwt_secret_key = Column(String, nullable=False)
    encryption_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic models for request/response
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.STANDARD

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    subscription_tier: UserRole
    api_quota: int
    api_usage: int

class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scopes: List[APIKeyScope] = [APIKeyScope.READ]
    expires_at: Optional[datetime] = None
    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_requests_per_hour: Optional[int] = None
    rate_limit_requests_per_day: Optional[int] = None

class APIKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    description: Optional[str]
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    created_at: datetime
    rate_limit: Dict[str, int]

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class RateLimitConfig(BaseModel):
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10

class SecurityConfig(BaseModel):
    require_https: bool = True
    allowed_origins: List[str] = ["*"]
    allowed_ips: Optional[List[str]] = None
    max_request_size_mb: int = 10
    session_timeout_minutes: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
import jwt
import bcrypt
import secrets
import redis
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from cryptography.fernet import Fernet

from .auth_models import User, APIKey, UserSession, AuditLog, UserRole, APIKeyScope, SystemConfig
from .db import get_db
from .security import get_redis_client

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.redis_client = get_redis_client()
        self.jwt_secret = self._get_jwt_secret()
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.encryption_key = self._get_encryption_key()
        
    def _get_jwt_secret(self) -> str:
        """Get JWT secret from system config or environment"""
        try:
            with get_db().__next__() as db:
                config = db.query(SystemConfig).first()
                if config and config.jwt_secret_key:
                    return config.jwt_secret_key
        except Exception as e:
            logger.warning(f"Could not get JWT secret from config: {e}")
        
        # Fallback to environment variable
        import os
        return os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    
    def _get_encryption_key(self) -> str:
        """Get encryption key from system config or environment"""
        try:
            with get_db().__next__() as db:
                config = db.query(SystemConfig).first()
                if config and config.encryption_key:
                    return config.encryption_key
        except Exception as e:
            logger.warning(f"Could not get encryption key from config: {e}")
        
        # Fallback to environment variable
        import os
        key = os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32))
        return key

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def create_user(self, db: Session, user_data: dict) -> User:
        """Create a new user"""
        # Check if user already exists
        if db.query(User).filter(User.email == user_data['email']).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if db.query(User).filter(User.username == user_data['username']).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Validate password strength
        if len(user_data['password']) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Hash password
        password_hash = self.hash_password(user_data['password'])
        
        # Create user
        user = User(
            email=user_data['email'],
            username=user_data['username'],
            password_hash=password_hash,
            full_name=user_data.get('full_name'),
            role=user_data.get('role', UserRole.STANDARD),
            is_active=True,
            is_verified=False,  # Require email verification
            subscription_tier=user_data.get('role', UserRole.STANDARD),
            api_quota=self._get_default_quota_for_role(user_data.get('role', UserRole.STANDARD))
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Log user creation
        self._log_audit_event(
            db=db,
            user_id=user.id,
            action="user_created",
            resource="user",
            resource_id=user.id,
            details={"email": user.email, "role": user.role.value}
        )
        
        return user

    def authenticate_user(self, db: Session, email: str, password: str) -> User:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        if not self.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Log successful login
        self._log_audit_event(
            db=db,
            user_id=user.id,
            action="user_login",
            resource="user",
            resource_id=user.id,
            details={"email": email}
        )
        
        return user

    def create_api_key(self, db: Session, user_id: str, key_data: dict) -> APIKey:
        """Create a new API key for user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check API key limit
        user_api_keys = db.query(APIKey).filter(APIKey.user_id == user_id).count()
        system_config = db.query(SystemConfig).first()
        max_keys = system_config.max_api_keys_per_user if system_config else 5
        
        if user_api_keys >= max_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum API key limit ({max_keys}) reached"
            )
        
        # Generate API key
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]
        
        # Encrypt sensitive data
        fernet = Fernet(self.encryption_key.encode())
        
        api_key = APIKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=key_data['name'],
            description=key_data.get('description'),
            user_id=user_id,
            scopes=json.dumps([scope.value for scope in key_data.get('scopes', [APIKeyScope.READ])]),
            is_active=True,
            expires_at=key_data.get('expires_at'),
            rate_limit_requests_per_minute=key_data.get('rate_limit_requests_per_minute', 60),
            rate_limit_requests_per_hour=key_data.get('rate_limit_requests_per_hour', 1000),
            rate_limit_requests_per_day=key_data.get('rate_limit_requests_per_day', 10000),
            allowed_ips=json.dumps(key_data.get('allowed_ips', [])) if key_data.get('allowed_ips') else None,
            allowed_origins=json.dumps(key_data.get('allowed_origins', [])) if key_data.get('allowed_origins') else None
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        # Store raw key securely (only return it once)
        self._store_raw_key_temporarily(api_key.id, raw_key)
        
        # Log API key creation
        self._log_audit_event(
            db=db,
            user_id=user_id,
            action="api_key_created",
            resource="api_key",
            resource_id=api_key.id,
            details={"name": key_data['name'], "scopes": api_key.scopes}
        )
        
        return api_key, raw_key

    def _store_raw_key_temporarily(self, api_key_id: str, raw_key: str):
        """Store raw API key temporarily in Redis"""
        try:
            self.redis_client.setex(
                f"raw_api_key:{api_key_id}",
                300,  # 5 minutes
                raw_key
            )
        except Exception as e:
            logger.error(f"Failed to store raw API key: {e}")

    def get_raw_api_key(self, api_key_id: str) -> Optional[str]:
        """Get raw API key from Redis (only available once)"""
        try:
            raw_key = self.redis_client.get(f"raw_api_key:{api_key_id}")
            if raw_key:
                # Delete after retrieval
                self.redis_client.delete(f"raw_api_key:{api_key_id}")
                return raw_key.decode()
        except Exception as e:
            logger.error(f"Failed to get raw API key: {e}")
        return None

    def validate_api_key(self, db: Session, raw_key: str) -> Optional[APIKey]:
        """Validate API key and return API key object"""
        try:
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            api_key = db.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()
            
            if not api_key:
                return None
            
            # Check expiration
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return None
            
            # Update last used timestamp
            api_key.last_used = datetime.utcnow()
            api_key.usage_count += 1
            db.commit()
            
            return api_key
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None

    def create_session(self, db: Session, user: User, ip_address: str, user_agent: str) -> UserSession:
        """Create user session"""
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session

    def create_jwt_tokens(self, user: User) -> dict:
        """Create JWT access and refresh tokens"""
        now = datetime.utcnow()
        
        access_token_payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
            "type": "access"
        }
        
        refresh_token_payload = {
            "sub": user.id,
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days),
            "type": "refresh"
        }
        
        access_token = jwt.encode(access_token_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        refresh_token = jwt.encode(refresh_token_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

    def verify_jwt_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def check_rate_limit(self, identifier: str, config: dict, redis_key: str) -> bool:
        """Check rate limit using sliding window algorithm"""
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=1)
            
            # Clean old entries
            self.redis_client.zremrangebyscore(
                redis_key,
                0,
                window_start.timestamp()
            )
            
            # Get current count
            current_count = self.redis_client.zcard(redis_key)
            
            if current_count >= config.get('requests_per_minute', 60):
                return False
            
            # Add current request
            self.redis_client.zadd(redis_key, {str(now.timestamp()): now.timestamp()})
            self.redis_client.expire(redis_key, 3600)  # 1 hour expiry
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow request if rate limiting fails

    def check_permission(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user has required role"""
        role_hierarchy = {
            UserRole.READONLY: 0,
            UserRole.TRIAL: 1,
            UserRole.STANDARD: 2,
            UserRole.PREMIUM: 3,
            UserRole.ADMIN: 4
        }
        
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

    def _log_audit_event(self, db: Session, **kwargs):
        """Log audit event"""
        try:
            audit_log = AuditLog(**kwargs)
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def get_system_config(self, db: Session) -> SystemConfig:
        """Get or create system configuration"""
        config = db.query(SystemConfig).first()
        if not config:
            config = SystemConfig(
                public_readonly_mode=False,
                allow_registration=True,
                default_user_role=UserRole.STANDARD,
                trial_period_days=14,
                max_api_keys_per_user=5,
                require_email_verification=True,
                password_min_length=8,
                session_timeout_hours=24,
                jwt_secret_key=secrets.token_urlsafe(32),
                encryption_key=secrets.token_urlsafe(32)
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    def _get_default_quota_for_role(self, role: UserRole) -> int:
        """Get default API quota based on role"""
        quotas = {
            UserRole.READONLY: 100,
            UserRole.TRIAL: 500,
            UserRole.STANDARD: 1000,
            UserRole.PREMIUM: 5000,
            UserRole.ADMIN: 10000
        }
        return quotas.get(role, 1000)

# Global auth service instance
auth_service = AuthService()
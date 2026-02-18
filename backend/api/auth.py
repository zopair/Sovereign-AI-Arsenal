from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import secrets
import json
from datetime import datetime, timedelta

from ..db import get_db
from ..auth_models import User, APIKey, UserRole, APIKeyScope, UserCreate, UserLogin, APIKeyCreate, APIKeyResponse
from ..auth_service import AuthService
from ..middleware.security import SecurityMiddleware

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()

# Initialize auth service
auth_service = AuthService()

@router.post("/register", response_model=dict)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    try:
        # Check if registration is allowed
        config = auth_service.get_system_config(db)
        if not config.allow_registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is disabled"
            )
        
        # Create user
        user = auth_service.create_user(db, user_data.dict())
        
        # Create session
        session = auth_service.create_session(
            db, 
            user, 
            "registration", 
            "api"
        )
        
        # Generate tokens
        tokens = auth_service.create_jwt_tokens(user)
        
        # Send verification email (in production)
        # await email_service.send_verification_email(user.email)
        
        return {
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
                "is_verified": user.is_verified
            },
            "tokens": tokens,
            "session_id": session.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=dict)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    try:
        # Authenticate user
        user = auth_service.authenticate_user(db, user_data.email, user_data.password)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Create session
        session = auth_service.create_session(
            db, 
            user, 
            "login", 
            "api"
        )
        
        # Generate tokens
        tokens = auth_service.create_jwt_tokens(user)
        
        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
                "is_verified": user.is_verified,
                "last_login": user.last_login
            },
            "tokens": tokens,
            "session_id": session.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = auth_service.verify_jwt_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Generate new tokens
        tokens = auth_service.create_jwt_tokens(user)
        
        return {
            "message": "Token refreshed successfully",
            "tokens": tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        # Verify refresh token
        payload = auth_service.verify_jwt_token(refresh_token)
        
        # Remove session from database
        db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).delete()
        db.commit()
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )

@router.get("/me", response_model=dict)
async def get_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    try:
        # Get user's API keys
        api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
        
        return {
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username,
                "full_name": current_user.full_name,
                "role": current_user.role.value,
                "is_active": current_user.is_active,
                "is_verified": current_user.is_verified,
                "last_login": current_user.last_login,
                "created_at": current_user.created_at,
                "subscription_tier": current_user.subscription_tier.value,
                "api_quota": current_user.api_quota,
                "api_usage": current_user.api_usage
            },
            "api_keys": [
                {
                    "id": api_key.id,
                    "name": api_key.name,
                    "key_prefix": api_key.key_prefix,
                    "scopes": json.loads(api_key.scopes),
                    "is_active": api_key.is_active,
                    "expires_at": api_key.expires_at,
                    "last_used": api_key.last_used,
                    "usage_count": api_key.usage_count,
                    "created_at": api_key.created_at
                }
                for api_key in api_keys
            ]
        }
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    try:
        # Check user's API key limit
        user_api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).count()
        config = auth_service.get_system_config(db)
        max_keys = config.max_api_keys_per_user
        
        if user_api_keys >= max_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum API key limit ({max_keys}) reached"
            )
        
        # Create API key
        api_key, raw_key = auth_service.create_api_key(db, current_user.id, key_data.dict())
        
        return {
            "id": api_key.id,
            "key": raw_key,  # Only return the raw key once
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "scopes": json.loads(api_key.scopes),
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at,
            "created_at": api_key.created_at,
            "message": "API key created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's API keys"""
    try:
        api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
        
        return [
            {
                "id": api_key.id,
                "name": api_key.name,
                "key_prefix": api_key.key_prefix,
                "scopes": json.loads(api_key.scopes),
                "is_active": api_key.is_active,
                "expires_at": api_key.expires_at,
                "last_used": api_key.last_used,
                "usage_count": api_key.usage_count,
                "created_at": api_key.created_at
            }
            for api_key in api_keys
        ]
        
    except Exception as e:
        logger.error(f"List API keys error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )

@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    try:
        api_key = db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        db.delete(api_key)
        db.commit()
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )

@router.put("/api-keys/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: str,
    key_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an API key"""
    try:
        api_key = db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Update allowed fields
        if 'name' in key_data:
            api_key.name = key_data['name']
        if 'description' in key_data:
            api_key.description = key_data['description']
        if 'scopes' in key_data:
            api_key.scopes = json.dumps([scope.value for scope in key_data['scopes']])
        if 'is_active' in key_data:
            api_key.is_active = key_data['is_active']
        if 'expires_at' in key_data:
            api_key.expires_at = key_data['expires_at']
        
        # Update rate limits if provided
        if 'rate_limit_requests_per_minute' in key_data:
            api_key.rate_limit_requests_per_minute = key_data['rate_limit_requests_per_minute']
        if 'rate_limit_requests_per_hour' in key_data:
            api_key.rate_limit_requests_per_hour = key_data['rate_limit_requests_per_hour']
        if 'rate_limit_requests_per_day' in key_data:
            api_key.rate_limit_requests_per_day = key_data['rate_limit_requests_per_day']
        
        api_key.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(api_key)
        
        return {
            "id": api_key.id,
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "scopes": json.loads(api_key.scopes),
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at,
            "last_used": api_key.last_used,
            "usage_count": api_key.usage_count,
            "created_at": api_key.created_at,
            "message": "API key updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key"
        )

@router.get("/system/config")
async def get_system_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system configuration (admin only)"""
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        config = auth_service.get_system_config(db)
        
        return {
            "public_readonly_mode": config.public_readonly_mode,
            "allow_registration": config.allow_registration,
            "default_user_role": config.default_user_role.value,
            "trial_period_days": config.trial_period_days,
            "max_api_keys_per_user": config.max_api_keys_per_user,
            "require_email_verification": config.require_email_verification,
            "password_min_length": config.password_min_length,
            "session_timeout_hours": config.session_timeout_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system configuration"
        )

@router.put("/system/config")
async def update_system_config(
    config_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update system configuration (admin only)"""
    try:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        config = auth_service.get_system_config(db)
        
        # Update allowed fields
        if 'public_readonly_mode' in config_data:
            config.public_readonly_mode = config_data['public_readonly_mode']
        if 'allow_registration' in config_data:
            config.allow_registration = config_data['allow_registration']
        if 'trial_period_days' in config_data:
            config.trial_period_days = config_data['trial_period_days']
        if 'max_api_keys_per_user' in config_data:
            config.max_api_keys_per_user = config_data['max_api_keys_per_user']
        if 'require_email_verification' in config_data:
            config.require_email_verification = config_data['require_email_verification']
        if 'password_min_length' in config_data:
            config.password_min_length = config_data['password_min_length']
        if 'session_timeout_hours' in config_data:
            config.session_timeout_hours = config_data['session_timeout_hours']
        
        config.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "System configuration updated successfully",
            "config": {
                "public_readonly_mode": config.public_readonly_mode,
                "allow_registration": config.allow_registration,
                "trial_period_days": config.trial_period_days,
                "max_api_keys_per_user": config.max_api_keys_per_user,
                "require_email_verification": config.require_email_verification,
                "password_min_length": config.password_min_length,
                "session_timeout_hours": config.session_timeout_hours
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update system config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system configuration"
        )

# Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = security,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        # Verify JWT token
        payload = auth_service.verify_jwt_token(credentials.credentials)
        
        # Get user from database
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user
        
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
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
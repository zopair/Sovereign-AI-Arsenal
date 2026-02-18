import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import json
import ipaddress
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .auth_service import AuthService
from .auth_models import User, APIKey, UserRole, APIKeyScope
from .db import get_db

logger = logging.getLogger(__name__)

# Initialize Redis for rate limiting
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=1,
        decode_responses=True
    )
except Exception as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

class RateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.block_duration = 300  # 5 minutes
        
        # Rate limit configurations
        self.limits = {
            'anonymous': {
                'requests_per_minute': 20,
                'requests_per_hour': 200,
                'requests_per_day': 1000
            },
            'trial': {
                'requests_per_minute': 60,
                'requests_per_hour': 600,
                'requests_per_day': 3000
            },
            'standard': {
                'requests_per_minute': 120,
                'requests_per_hour': 1200,
                'requests_per_day': 6000
            },
            'premium': {
                'requests_per_minute': 300,
                'requests_per_hour': 3000,
                'requests_per_day': 15000
            },
            'admin': {
                'requests_per_minute': 1000,
                'requests_per_hour': 10000,
                'requests_per_day': 50000
            }
        }
        
        # Special limits for expensive operations
        self.operation_limits = {
            'sandbox_analyze': {
                'requests_per_hour': 10,
                'requests_per_day': 50
            },
            'discovery': {
                'requests_per_hour': 20,
                'requests_per_day': 100
            },
            'bulk_analyze': {
                'requests_per_hour': 5,
                'requests_per_day': 25
            }
        }

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked"""
        if not self.redis_client:
            return False
            
        block_key = f"blocked:{identifier}"
        return self.redis_client.exists(block_key)

    def block_identifier(self, identifier: str, duration: Optional[int] = None):
        """Block identifier for specified duration"""
        if not self.redis_client:
            return
            
        block_key = f"blocked:{identifier}"
        duration = duration or self.block_duration
        self.redis_client.setex(block_key, duration, "1")

    def unblock_identifier(self, identifier: str):
        """Unblock identifier"""
        if not self.redis_client:
            return
            
        block_key = f"blocked:{identifier}"
        self.redis_client.delete(block_key)

    def check_rate_limit_sliding_window(
        self, 
        identifier: str, 
        limit_config: Dict[str, int],
        window_seconds: int = 60
    ) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using sliding window algorithm"""
        if not self.redis_client:
            return True, {}
            
        now = time.time()
        window_start = now - window_seconds
        
        # Use sorted set for sliding window
        key = f"rate_limit:{identifier}"
        
        # Remove old entries
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Get current count
        current_count = self.redis_client.zcard(key)
        
        if current_count >= limit_config['requests_per_minute']:
            return False, {
                'limit': limit_config['requests_per_minute'],
                'current': current_count,
                'reset_time': now + window_seconds,
                'window_seconds': window_seconds
            }
        
        # Add current request
        self.redis_client.zadd(key, {str(now): now})
        self.redis_client.expire(key, window_seconds * 2)  # 2x window size
        
        return True, {
            'limit': limit_config['requests_per_minute'],
            'current': current_count + 1,
            'remaining': limit_config['requests_per_minute'] - current_count,
            'reset_time': now + window_seconds
        }

    def check_operation_limit(
        self, 
        identifier: str, 
        operation: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit for specific operation"""
        if not self.redis_client:
            return True, {}
            
        limit_config = self.operation_limits.get(operation, {})
        if not limit_config:
            return True, {}
            
        key = f"op_limit:{identifier}:{operation}"
        now = time.time()
        hour_seconds = 3600
        
        # Use hourly window for operations
        window_start = now - hour_seconds
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        current_count = self.redis_client.zcard(key)
        
        if current_count >= limit_config.get('requests_per_hour', 100):
            return False, {
                'limit': limit_config.get('requests_per_hour', 100),
                'current': current_count,
                'reset_time': now + hour_seconds
            }
        
        # Add current request
        self.redis_client.zadd(key, {str(now): now})
        self.redis_client.expire(key, hour_seconds * 2)
        
        return True, {
            'limit': limit_config.get('requests_per_hour', 100),
            'current': current_count + 1,
            'remaining': limit_config.get('requests_per_hour', 100) - current_count
        }

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for authentication, authorization, and rate limiting"""
    
    def __init__(self, app, auth_service: AuthService):
        super().__init__(app)
        self.auth_service = auth_service
        self.rate_limiter = RateLimiter()
        
        # Security configuration
        self.security_config = {
            'require_https': True,
            'allowed_origins': ["*"],  # Configure based on your needs
            'allowed_ips': None,  # Specific IPs if needed
            'max_request_size': 10 * 1024 * 1024,  # 10MB
            'session_timeout_minutes': 30,
            'max_login_attempts': 5,
            'lockout_duration_minutes': 15,
            'cors_origins': ["*"],
            'cors_methods': ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            'cors_headers': ["*"]
        }

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if self.rate_limiter.is_blocked(client_ip):
            return Response(
                content={"error": "IP address blocked"},
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Check public read-only mode
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            if self._is_public_readonly_mode():
                return Response(
                    content={"error": "System is in read-only mode"},
                    status_code=status.HTTP_403_FORBIDDEN
                )
        
        # Get authentication info
        auth_info = await self._get_auth_info(request)
        
        # Check rate limiting
        if not await self._check_rate_limit(request, auth_info, client_ip):
            return Response(
                content={"error": "Rate limit exceeded"},
                status_code=status.HTTP_429_TOO_MANY,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60)
                }
            )
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.security_config['max_request_size']:
            return Response(
                content={"error": "Request too large"},
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request for audit
        await self._log_request(request, response, auth_info, process_time)
        
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        client_host = request.client.host if request.client else "unknown"
        return client_host

    async def _get_auth_info(self, request: Request) -> Dict[str, Any]:
        """Get authentication information from request"""
        auth_info = {
            'authenticated': False,
            'user': None,
            'api_key': None,
            'role': None,
            'scopes': []
        }
        
        # Check for API key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key:
            with get_db().__next__() as db:
                api_key_obj = self.auth_service.validate_api_key(db, api_key)
                if api_key_obj:
                    auth_info.update({
                        'authenticated': True,
                        'api_key': api_key_obj,
                        'user': api_key_obj.user,
                        'role': api_key_obj.user.role,
                        'scopes': json.loads(api_key_obj.scopes),
                        'rate_limits': {
                            'requests_per_minute': api_key_obj.rate_limit_requests_per_minute,
                            'requests_per_hour': api_key_obj.rate_limit_requests_per_hour,
                            'requests_per_day': api_key_obj.rate_limit_requests_per_day
                        }
                    })
        
        # Check for JWT token authentication
        elif "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = self.auth_service.verify_jwt_token(token)
                    with get_db().__next__() as db:
                        user = db.query(User).filter(User.id == payload["sub"]).first()
                        if user:
                            auth_info.update({
                                'authenticated': True,
                                'user': user,
                                'role': user.role,
                                'jwt_payload': payload
                            })
                except Exception as e:
                    logger.warning(f"JWT validation failed: {e}")
        
        return auth_info

    async def _check_rate_limit(self, request: request, auth_info: Dict[str, Any], client_ip: str) -> bool:
        """Check rate limiting based on authentication and request type"""
        try:
            # Get rate limit configuration
            if auth_info['authenticated']:
                if auth_info['api_key']:
                    # Use API key specific limits
                    limits = auth_info['rate_limits']
                    limit_key = f"api_key:{auth_info['api_key'].id}"
                else:
                    # Use user role limits
                    limits = self.rate_limiter.limits.get(auth_info['role'].value, self.rate_limiter.limits['standard'])
                    limit_key = f"user:{auth_info['user'].id}"
            else:
                # Use anonymous limits
                limits = self.rate_limiter.limits['anonymous']
                limit_key = f"anonymous:{client_ip}"
            
            # Check operation-specific limits for expensive operations
            operation = request.url.path.split('/')[-1]
            if operation in ['sandbox-analyze', 'discover', 'bulk-analyze']:
                operation_key = f"operation:{operation}:{limit_key}"
                success, _ = self.rate_limiter.check_operation_limit(operation_key, operation)
                if not success:
                    return False
            
            # Check general rate limit
            success, _ = self.rate_limiter.check_rate_limit_sliding_window(
                limit_key, 
                limits,
                60  # 1 minute window
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow request if rate limiting fails

    def _is_public_readonly_mode(self) -> bool:
        """Check if system is in public read-only mode"""
        try:
            with get_db().__next__() as db:
                config = self.auth_service.get_system_config(db)
                return config.public_readonly_mode
        except Exception as e:
            logger.error(f"Error checking public read-only mode: {e}")
            return False

    async def _log_request(self, request: Request, response: Response, auth_info: Dict[str, Any], process_time: float):
        """Log request for audit trail"""
        try:
            log_data = {
                'method': request.method,
                'url': str(request.url),
                'status_code': response.status_code,
                'process_time_ms': process_time * 1000,
                'client_ip': self._get_client_ip(request),
                'user_agent': request.headers.get("user-agent", ""),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if auth_info['authenticated']:
                log_data.update({
                    'user_id': auth_info['user'].id if auth_info['user'] else None,
                    'role': auth_info['role'].value if auth_info['role'] else None,
                    'authenticated': True
                })
            
            # Log to Redis for recent logs (optional)
            if self.redis_client:
                log_key = f"audit_log:{datetime.utcnow().strftime('%Y%m%d')}"
                self.redis_client.lpush(log_key, json.dumps(log_data))
                self.redis_client.expire(log_key, 86400)  # 24 hours
                
                # Keep only last 1000 entries
                self.redis_client.ltrim(log_key, 0, 1000)
            
            # Log to file for long-term storage (in production, use proper logging system)
            logger.info(f"Audit log: {log_data}")
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")

# Initialize rate limiter for slowapi
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter

# Rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else 60
        }
    )
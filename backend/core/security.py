import os
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecureTokenManager:
    """Secure management of sensitive tokens and API keys"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key.encode())
        self.token_cache = {}
        self.cache_expiry = {}
        
    def _get_or_create_key(self) -> str:
        """Get or create encryption key"""
        # Try to get key from environment
        key = os.getenv('ENCRYPTION_KEY')
        if key:
            return key
        
        # Try to get from file
        key_file = os.path.join(os.path.dirname(__file__), '..', '.encryption_key')
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                return f.read().strip()
        
        # Generate new key
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        
        # Save to file (with restricted permissions)
        try:
            with open(key_file, 'w') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Only owner can read/write
        except Exception as e:
            logger.warning(f"Could not save encryption key: {e}")
        
        return key
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token"""
        try:
            encrypted = self.cipher_suite.encrypt(token.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting token: {e}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token"""
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted = self.cipher_suite.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            raise
    
    def get_github_token(self, force_refresh: bool = False) -> Optional[str]:
        """Get GitHub token with caching"""
        cache_key = 'github_token'
        
        # Check cache
        if not force_refresh and self._is_cached_valid(cache_key):
            return self.token_cache[cache_key]
        
        # Get from environment
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            logger.warning("GitHub token not found in environment")
            return None
        
        # Validate token format
        if not token.startswith('ghp_') and not token.startswith('github_pat_'):
            logger.warning("Invalid GitHub token format")
            return None
        
        # Cache the token
        self.token_cache[cache_key] = token
        self.cache_expiry[cache_key] = datetime.utcnow() + timedelta(hours=1)
        
        return token
    
    def get_openai_token(self, force_refresh: bool = False) -> Optional[str]:
        """Get OpenAI token with caching"""
        cache_key = 'openai_token'
        
        # Check cache
        if not force_refresh and self._is_cached_valid(cache_key):
            return self.token_cache[cache_key]
        
        # Get from environment
        token = os.getenv('OPENAI_API_KEY')
        if not token:
            logger.warning("OpenAI token not found in environment")
            return None
        
        # Validate token format
        if not token.startswith('sk-'):
            logger.warning("Invalid OpenAI token format")
            return None
        
        # Cache the token
        self.token_cache[cache_key] = token
        self.cache_expiry[cache_key] = datetime.utcnow() + timedelta(hours=1)
        
        return token
    
    def get_database_credentials(self) -> Dict[str, str]:
        """Get database credentials securely"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'name': os.getenv('DB_NAME', 'sovereign_ai arsenal'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
    
    def get_redis_credentials(self) -> Dict[str, str]:
        """Get Redis credentials securely"""
        return {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': os.getenv('REDIS_PORT', '6379'),
            'password': os.getenv('REDIS_PASSWORD', '')
        }
    
    def mask_sensitive_data(self, data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
        """Mask sensitive data for logging"""
        if len(data) <= visible_chars:
            return mask_char * len(data)
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)
    
    async def validate_github_token_scope(self, token: str) -> bool:
        """Validate GitHub token has required scopes"""
        try:
            import aiohttp
            
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Test token with a simple API call
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.github.com/user', headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
                        
                        # Check for required scopes
                        required_scopes = ['public_repo', 'read:org']
                        has_required = any(scope in required_scopes for scope in scopes)
                        
                        if not has_required:
                            logger.warning(f"GitHub token missing required scopes. Current scopes: {scopes}")
                            return False
                        
                        logger.info(f"GitHub token validated for user: {user_data.get('login')}")
                        return True
                    else:
                        logger.error(f"GitHub token validation failed: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"Error validating GitHub token: {e}")
            return False
    
    def rotate_token(self, token_type: str) -> bool:
        """Rotate a token (placeholder for future implementation)"""
        # This would integrate with token rotation systems
        # For now, just clear cache to force refresh
        cache_key = f'{token_type}_token'
        if cache_key in self.token_cache:
            del self.token_cache[cache_key]
        if cache_key in self.cache_expiry:
            del self.cache_expiry[cache_key]
        
        logger.info(f"Token rotation triggered for {token_type}")
        return True
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached token is still valid"""
        if cache_key not in self.token_cache or cache_key not in self.cache_expiry:
            return False
        
        if datetime.utcnow() > self.cache_expiry[cache_key]:
            # Expired, remove from cache
            del self.token_cache[cache_key]
            del self.cache_expiry[cache_key]
            return False
        
        return True
    
    def clear_cache(self):
        """Clear all cached tokens"""
        self.token_cache.clear()
        self.cache_expiry.clear()
        logger.info("Token cache cleared")
    
    def get_token_status(self) -> Dict[str, Any]:
        """Get status of all tokens"""
        return {
            'github_token_available': bool(self.get_github_token()),
            'openai_token_available': bool(self.get_openai_token()),
            'cached_tokens': list(self.token_cache.keys()),
            'cache_expiry': {
                key: expiry.isoformat() 
                for key, expiry in self.cache_expiry.items()
            }
        }

class GitHubTokenRotator:
    """Handles GitHub token rotation for long-running processes"""
    
    def __init__(self, token_manager: SecureTokenManager):
        self.token_manager = token_manager
        self.rotation_interval = timedelta(hours=6)  # Rotate every 6 hours
        self.last_rotation = {}
    
    def should_rotate_token(self, token_type: str) -> bool:
        """Check if token should be rotated"""
        if token_type not in self.last_rotation:
            return True
        
        return datetime.utcnow() - self.last_rotation[token_type] > self.rotation_interval
    
    def rotate_if_needed(self, token_type: str) -> Optional[str]:
        """Rotate token if needed"""
        if not self.should_rotate_token(token_type):
            return self.token_manager.get_github_token() if token_type == 'github' else None
        
        # Perform rotation
        if self.token_manager.rotate_token(token_type):
            self.last_rotation[token_type] = datetime.utcnow()
            return self.token_manager.get_github_token() if token_type == 'github' else None
        
        return None

# Global token manager instance
token_manager = None

def init_token_manager(encryption_key: Optional[str] = None) -> SecureTokenManager:
    """Initialize global token manager instance"""
    global token_manager
    token_manager = SecureTokenManager(encryption_key)
    return token_manager

def get_token_manager() -> SecureTokenManager:
    """Get global token manager instance"""
    if token_manager is None:
        raise RuntimeError("Token manager not initialized. Call init_token_manager() first.")
    return token_manager

# Decorator for secure token handling
def require_github_token(func):
    """Decorator to ensure GitHub token is available"""
    def wrapper(*args, **kwargs):
        manager = get_token_manager()
        token = manager.get_github_token()
        if not token:
            raise ValueError("GitHub token required but not available")
        return func(*args, **kwargs)
    return wrapper

def require_openai_token(func):
    """Decorator to ensure OpenAI token is available"""
    def wrapper(*args, **kwargs):
        manager = get_token_manager()
        token = manager.get_openai_token()
        if not token:
            raise ValueError("OpenAI token required but not available")
        return func(*args, **kwargs)
    return wrapper

# Context manager for secure token operations
class SecureTokenContext:
    """Context manager for secure token operations"""
    
    def __init__(self, token_manager: SecureTokenManager):
        self.token_manager = token_manager
        self.original_tokens = {}
    
    def __enter__(self):
        # Backup current environment variables
        self.original_tokens = {
            'GITHUB_TOKEN': os.getenv('GITHUB_TOKEN'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD'),
            'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD')
        }
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original environment variables
        for key, value in self.original_tokens.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # Clear token cache
        self.token_manager.clear_cache()
    
    def get_secure_github_token(self) -> Optional[str]:
        """Get GitHub token securely within context"""
        return self.token_manager.get_github_token()
    
    def get_secure_openai_token(self) -> Optional[str]:
        """Get OpenAI token securely within context"""
        return self.token_manager.get_openai_token()

# Logging formatter that masks sensitive data
class SecureFormatter(logging.Formatter):
    """Custom formatter that masks sensitive data"""
    
    def __init__(self, *args, **kwargs):
        self.token_manager = get_token_manager() if token_manager else None
        super().__init__(*args, **kwargs)
    
    def format(self, record):
        message = super().format(record)
        
        # Mask common sensitive patterns
        sensitive_patterns = [
            (r'(ghp_[a-zA-Z0-9]{36})', r'ghp_****************'),
            (r'(sk-[a-zA-Z0-9]{48})', r'sk-****************************************'),
            (r'(github_pat_[a-zA-Z0-9_]{82})', r'github_pat_**************************************************'),
            (r'(password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)', r'\1***'),
        ]
        
        import re
        for pattern, replacement in sensitive_patterns:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        return message
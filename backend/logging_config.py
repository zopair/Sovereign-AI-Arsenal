import logging
import logging.handlers
import os
import yaml
from datetime import datetime

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Load configuration
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        config = {}
    
    log_config = config.get('logging', {})
    log_level = getattr(logging, os.getenv('LOG_LEVEL', log_config.get('level', 'INFO')).upper())
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file', 'logs/app.log')
    max_size = log_config.get('max_size', '10MB')
    backup_count = log_config.get('backup_count', 5)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Convert max_size to bytes
    size_map = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    size_unit = max_size[-2:].upper()
    size_value = int(max_size[:-2])
    max_bytes = size_value * size_map.get(size_unit, 1024**2)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            # Console handler
            logging.StreamHandler(),
            
            # Rotating file handler
            logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            ),
            
            # Error file handler
            logging.handlers.RotatingFileHandler(
                filename='logs/errors.log',
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8',
                level=logging.ERROR
            ),
            
            # API access log
            logging.handlers.RotatingFileHandler(
                filename='logs/api.log',
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
        ]
    )
    
    # Set specific logger levels
    loggers = {
        'uvicorn': logging.INFO,
        'uvicorn.access': logging.INFO,
        'sqlalchemy.engine': logging.WARNING,
        'sqlalchemy.pool': logging.WARNING,
        'github': logging.INFO,
        'openai': logging.WARNING,
        'chromadb': logging.WARNING,
        'sentence_transformers': logging.WARNING
    }
    
    for logger_name, level in loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Create custom formatters
    class DetailedFormatter(logging.Formatter):
        """Custom formatter with detailed information"""
        
        def format(self, record):
            # Add extra fields
            record.timestamp = datetime.utcnow().isoformat()
            record.module_name = record.module if hasattr(record, 'module') else 'unknown'
            record.function_name = record.funcName if hasattr(record, 'funcName') else 'unknown'
            
            return super().format(record)
    
    # Create formatters
    detailed_format = '%(timestamp)s - %(name)s - %(module_name)s - %(function_name)s - %(levelname)s - %(message)s'
    simple_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    detailed_formatter = DetailedFormatter(detailed_format)
    simple_formatter = logging.Formatter(simple_format)
    
    # Apply formatters to handlers
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setFormatter(simple_formatter)
        else:
            handler.setFormatter(detailed_formatter)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Max file size: {max_size}")
    logger.info(f"Backup count: {backup_count}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

# Logger wrapper for structured logging
class StructuredLogger:
    """Structured logger for consistent log formatting"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        extra = {'structured_data': kwargs} if kwargs else {}
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data"""
        extra = {'structured_data': kwargs} if kwargs else {}
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data"""
        extra = {'structured_data': kwargs} if kwargs else {}
        self.logger.warning(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data"""
        extra = {'structured_data': kwargs} if kwargs else {}
        self.logger.debug(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured data"""
        extra = {'structured_data': kwargs} if kwargs else {}
        self.logger.critical(message, extra=extra)

# Performance monitoring decorator
def log_performance(func):
    """Decorator to log function performance"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    'structured_data': {
                        'function': func.__name__,
                        'duration_seconds': duration,
                        'status': 'success'
                    }
                }
            )
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(
                f"Function {func.__name__} failed with error: {str(e)}",
                extra={
                    'structured_data': {
                        'function': func.__name__,
                        'duration_seconds': duration,
                        'status': 'error',
                        'error': str(e)
                    }
                }
            )
            
            raise
    
    return wrapper

# API request logging middleware
class APILoggingMiddleware:
    """Middleware for logging API requests and responses"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('api')
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            import time
            
            # Extract request information
            start_time = time.time()
            client_ip = scope.get('client', ('', ''))[0]
            method = scope['method']
            path = scope['path']
            query_string = scope.get('query_string', b'').decode()
            
            # Log request
            self.logger.info(
                f"API Request: {method} {path}",
                extra={
                    'structured_data': {
                        'type': 'request',
                        'method': method,
                        'path': path,
                        'query': query_string,
                        'client_ip': client_ip,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            )
            
            # Process request
            try:
                await self.app(scope, receive, send)
                
                # Log successful response
                duration = time.time() - start_time
                self.logger.info(
                    f"API Response: {method} {path} - Success",
                    extra={
                        'structured_data': {
                            'type': 'response',
                            'method': method,
                            'path': path,
                            'status': 'success',
                            'duration_seconds': duration,
                            'client_ip': client_ip
                        }
                    }
                )
                
            except Exception as e:
                # Log error response
                duration = time.time() - start_time
                self.logger.error(
                    f"API Response: {method} {path} - Error: {str(e)}",
                    extra={
                        'structured_data': {
                            'type': 'response',
                            'method': method,
                            'path': path,
                            'status': 'error',
                            'error': str(e),
                            'duration_seconds': duration,
                            'client_ip': client_ip
                        }
                    }
                )
                
                raise
        else:
            await self.app(scope, receive, send)

# Database query logging
class DatabaseLogger:
    """Logger for database operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('database')
    
    def log_query(self, query: str, params: dict = None, duration: float = None):
        """Log database query"""
        self.logger.debug(
            f"Database query executed",
            extra={
                'structured_data': {
                    'type': 'database_query',
                    'query': query[:200] + '...' if len(query) > 200 else query,
                    'params': params,
                    'duration_seconds': duration
                }
            }
        )
    
    def log_error(self, operation: str, error: Exception):
        """Log database error"""
        self.logger.error(
            f"Database error during {operation}: {str(error)}",
            extra={
                'structured_data': {
                    'type': 'database_error',
                    'operation': operation,
                    'error': str(error)
                }
            }
        )

# GitHub API logging
class GitHubLogger:
    """Logger for GitHub API operations"""
    
    def __init__(self):
        self.logger = logging.getLogger('github')
    
    def log_request(self, endpoint: str, method: str = 'GET'):
        """Log GitHub API request"""
        self.logger.info(
            f"GitHub API request: {method} {endpoint}",
            extra={
                'structured_data': {
                    'type': 'github_request',
                    'method': method,
                    'endpoint': endpoint,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        )
    
    def log_response(self, endpoint: str, status_code: int, duration: float):
        """Log GitHub API response"""
        self.logger.info(
            f"GitHub API response: {endpoint} - {status_code}",
            extra={
                'structured_data': {
                    'type': 'github_response',
                    'endpoint': endpoint,
                    'status_code': status_code,
                    'duration_seconds': duration
                }
            }
        )
    
    def log_error(self, endpoint: str, error: Exception):
        """Log GitHub API error"""
        self.logger.error(
            f"GitHub API error: {endpoint} - {str(error)}",
            extra={
                'structured_data': {
                    'type': 'github_error',
                    'endpoint': endpoint,
                    'error': str(error)
                }
            }
        )

# Initialize logging when module is imported
setup_logging()
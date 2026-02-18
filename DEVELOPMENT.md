# Development Guide

This guide provides detailed information for developers working on the Sovereign AI Arsenal platform.

## 🏗️ Architecture Overview

### System Design Principles

1. **Modularity**: Each component has a single responsibility and clear interfaces
2. **Scalability**: Async operations, caching, and horizontal scaling support
3. **Maintainability**: Clean code, comprehensive tests, and documentation
4. **Reliability**: Error handling, logging, and graceful degradation
5. **Security**: Input validation, authentication, and data protection

### Component Interaction

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  Core Modules    │────│   External APIs │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Routes    │────│   Database       │────│   Vector Store  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)
- Git

### Local Development

1. **Clone and setup**
```bash
git clone <repository-url>
cd sovereign-ai-arsenal/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Database setup**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Create database
createdb sovereign_ai_arsenal

# Set up environment
cp .env.example .env
# Edit .env with your settings
```

3. **Run the application**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Development Tools

#### Code Formatting

```bash
# Format code
black .

# Sort imports
isort .

# Check formatting
black --check .
isort --check-only .
```

#### Linting and Type Checking

```bash
# Lint code
flake8 .

# Type checking
mypy .

# Run all checks
pre-commit run --all-files
```

#### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test
pytest tests/test_discovery.py

# Run with verbose output
pytest -v
```

## 📁 Code Organization

### Core Modules

#### Discovery Engine (`core/discovery.py`)

**Purpose**: Discover and fetch repository data from GitHub

**Key Functions**:
- `discover_ai_repositories()`: Main discovery function
- `get_repository_details()`: Fetch detailed repository info
- `get_repository_readme()`: Get README content
- `get_repository_contributors()`: Fetch contributor data

**Usage Example**:
```python
from core.discovery import GitHubDiscoveryEngine

engine = GitHubDiscoveryEngine(config)
repos = await engine.discover_ai_repositories(
    queries=["machine learning", "deep learning"],
    max_repos_per_query=100
)
```

#### Evaluator (`core/evaluator.py`)

**Purpose**: Comprehensive repository evaluation

**Key Functions**:
- `evaluate_repository()`: Full repository evaluation
- `_calculate_ai_relevance_score()`: AI relevance scoring
- `_calculate_quality_score()`: Code quality assessment

**Scoring Components**:
- Popularity (stars, forks, watchers)
- Activity (commits, updates, issues)
- Quality (documentation, license, structure)
- AI relevance (keywords, content analysis)

#### Classifier (`core/classifier.py`)

**Purpose**: AI-powered repository categorization

**Categories**:
- Machine Learning
- Deep Learning
- Computer Vision
- NLP
- Reinforcement Learning
- Data Science
- MLOps
- AI Frameworks
- Generative AI
- LLMs
- Robotics
- AI Ethics

**Usage Example**:
```python
from core.classifier import RepositoryClassifier

classifier = RepositoryClassifier(config)
classifications = classifier.classify_repository(repo_data)
```

#### Scorer (`core/scorer.py`)

**Purpose**: Comprehensive repository scoring

**Score Types**:
- Overall Score (weighted composite)
- Popularity Score
- Activity Score
- Community Score
- Trend Score
- Quality Score
- Potential Score

#### Trend Engine (`core/trend_engine.py`)

**Purpose**: Advanced trend analysis and predictions

**Features**:
- Growth pattern analysis
- Momentum calculation
- Acceleration detection
- Trend strength assessment
- Future predictions
- Risk assessment

#### LLM Analyzer (`core/llm_analyzer.py`)

**Purpose**: Deep AI-powered analysis using language models

**Analysis Types**:
- Executive summary
- Technical assessment
- Business potential
- Innovation evaluation
- Risk assessment
- Recommendations

### Database Layer

#### Models (`database/models.py`)

**Main Entities**:
- `Repository`: Core repository information
- `RepositoryMetrics`: Detailed metrics
- `Classification`: AI categories
- `Trend`: Historical data
- `Contributor`: Contributor info
- `Commit`: Commit history

#### Database Connection (`database/db.py`)

**Features**:
- Connection pooling
- Session management
- Transaction handling
- Health checks

#### Vector Store (`database/vector_store.py`)

**Purpose**: Semantic search using embeddings

**Features**:
- ChromaDB integration
- Embedding generation
- Similarity search
- Batch operations

## 🔄 API Development

### Adding New Endpoints

1. **Define endpoint in `api/routes.py`**
```python
@router.get("/custom-endpoint")
async def custom_endpoint(
    param: str = Query(...),
    db: Session = Depends(get_db)
):
    # Implementation
    return {"result": "success"}
```

2. **Add request/response models**
```python
from pydantic import BaseModel

class CustomRequest(BaseModel):
    name: str
    value: int

class CustomResponse(BaseModel):
    id: str
    status: str
```

3. **Add comprehensive error handling**
```python
try:
    # Business logic
    result = process_data(param)
    return CustomResponse(id=result.id, status="success")
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

### Best Practices

1. **Use dependency injection for database sessions**
2. **Implement proper error handling and logging**
3. **Validate all input parameters**
4. **Use Pydantic models for request/response**
5. **Add comprehensive docstrings**
6. **Implement rate limiting for expensive operations**
7. **Use background tasks for long-running operations**

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_discovery.py
│   ├── test_evaluator.py
│   ├── test_classifier.py
│   └── test_scorer.py
├── integration/
│   ├── test_api.py
│   ├── test_database.py
│   └── test_vector_store.py
├── e2e/
│   └── test_workflows.py
└── fixtures/
    ├── sample_repos.json
    └── mock_responses.json
```

### Writing Tests

#### Unit Tests

```python
import pytest
from core.evaluator import RepositoryEvaluator

class TestRepositoryEvaluator:
    def setup_method(self):
        self.config = {"scoring": {"weights": {"stars": 0.3}}}
        self.evaluator = RepositoryEvaluator(self.config)
    
    def test_calculate_popularity_score(self):
        repo_data = {"stargazers_count": 1000, "forks_count": 100}
        score = self.evaluator._calculate_popularity_score(repo_data)
        assert 0 <= score <= 1
        assert score > 0.5  # High popularity should give high score
    
    @pytest.mark.parametrize("stars,expected", [
        (0, 0.0),
        (10, 0.1),
        (1000, 0.8),
        (100000, 1.0)
    ])
    def test_popularity_score_edge_cases(self, stars, expected):
        repo_data = {"stargazers_count": stars, "forks_count": 0}
        score = self.evaluator._calculate_popularity_score(repo_data)
        assert abs(score - expected) < 0.1
```

#### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAPI:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_get_repositories(self):
        response = client.get("/api/v1/repositories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    async def test_discover_repositories(self):
        response = client.post("/api/v1/discover")
        assert response.status_code == 200
        assert "status" in response.json()
```

#### Mock External APIs

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_discovery_with_mock():
    mock_engine = AsyncMock()
    mock_engine.discover_ai_repositories.return_value = [
        {"id": 1, "name": "test-repo", "stars": 100}
    ]
    
    with patch('core.discovery.GitHubDiscoveryEngine', return_value=mock_engine):
        result = await mock_engine.discover_ai_repositories()
        assert len(result) == 1
        assert result[0]["name"] == "test-repo"
```

### Test Data Management

#### Fixtures

```python
@pytest.fixture
def sample_repository():
    return {
        "id": 12345,
        "name": "test-repo",
        "full_name": "user/test-repo",
        "description": "A test repository",
        "stargazers_count": 1000,
        "forks_count": 100,
        "language": "Python",
        "topics": ["machine-learning", "ai"]
    }

@pytest.fixture
def database_session():
    from database.db import get_db
    with get_db() as session:
        yield session
```

## 📊 Monitoring and Debugging

### Logging Strategy

#### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

def process_repository(repo_data):
    logger.info(
        "Processing repository",
        extra={
            "structured_data": {
                "repo_id": repo_data["id"],
                "repo_name": repo_data["name"],
                "operation": "process"
            }
        }
    )
```

#### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Function {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper
```

### Database Debugging

#### Query Analysis

```python
# Enable query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Analyze slow queries
from sqlalchemy import event
from engine import engine

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.5:  # Log slow queries
        logger.warning(f"Slow query: {total:.2f}s - {statement[:100]}")
```

## 🚀 Performance Optimization

### Database Optimization

#### Indexing Strategy

```sql
-- Composite indexes for common queries
CREATE INDEX idx_repositories_score_updated ON repositories(score, updated_at);
CREATE INDEX idx_classifications_category_confidence ON classifications(category, confidence);

-- Partial indexes for filtered queries
CREATE INDEX idx_active_repositories ON repositories(updated_at) WHERE NOT archived;
```

#### Connection Pooling

```python
# Optimize connection pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Base connections
    max_overflow=30,       # Additional connections under load
    pool_timeout=30,       # Wait time for connection
    pool_recycle=3600,     # Recycle connections every hour
    pool_pre_ping=True     # Validate connections
)
```

### Caching Strategy

#### Redis Caching

```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expiration=1800)
def get_repository_details(repo_id):
    # Expensive database operation
    return repository_service.get_details(repo_id)
```

### Async Optimization

#### Concurrent Processing

```python
import asyncio
from asyncio import Semaphore

async def process_repositories_batch(repos, batch_size=10):
    semaphore = Semaphore(batch_size)
    
    async def process_with_semaphore(repo):
        async with semaphore:
            return await process_repository(repo)
    
    tasks = [process_with_semaphore(repo) for repo in repos]
    return await asyncio.gather(*tasks)
```

## 🔒 Security Considerations

### Input Validation

```python
from pydantic import BaseModel, validator
import re

class RepositoryQuery(BaseModel):
    query: str
    limit: int = 100
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) < 2:
            raise ValueError('Query must be at least 2 characters')
        if len(v) > 1000:
            raise ValueError('Query too long')
        # Sanitize input
        if re.search(r'[<>"\']', v):
            raise ValueError('Invalid characters in query')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('Limit must be between 1 and 1000')
        return v
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/search")
@limiter.limit("100/minute")
async def search_repositories(request: Request, q: str):
    # Implementation
    pass
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=backend --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      run: |
        pip install safety bandit
        safety check -r requirements.txt
        bandit -r . -f json
  
  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t sovereign-ai-arsenal:${{ github.sha }} .
        docker tag sovereign-ai-arsenal:${{ github.sha }} sovereign-ai-arsenal:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push sovereign-ai-arsenal:${{ github.sha }}
        docker push sovereign-ai-arsenal:latest
```

This development guide provides comprehensive information for developers working on the Sovereign AI Arsenal platform. It covers architecture, setup, coding standards, testing, monitoring, and deployment best practices.
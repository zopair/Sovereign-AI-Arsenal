# Update backend/requirements.txt with Phase 2 dependencies
# Read existing requirements and append new ones

existing_requirements = """# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.1

# HTTP Client
httpx==0.25.2
aiohttp==3.9.1
requests==2.31.0

# AI/ML
openai==1.3.7
sentence-transformers==2.2.2
chromadb==0.4.18
numpy==1.24.4
scikit-learn==1.3.2

# Data Processing
pandas==2.1.4
pyyaml==6.0.1
python-dotenv==1.0.0
python-multipart==0.0.6

# Async Support
asyncio==3.4.3
asyncpg==0.29.0

# Utilities
python-dateutil==2.8.2
pytz==2023.3
click==8.1.7
rich==13.7.0
tqdm==4.66.1

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1

# Monitoring & Logging
prometheus-client==0.19.0
structlog==23.2.0

# Security
cryptography==41.0.8
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# Rate Limiting
slowapi==0.1.9

# Background Tasks
celery==5.3.4
redis==5.0.1

# Image Processing (for potential future features)
pillow==10.1.0

# Web Scraping (for potential data sources)
beautifulsoup4==4.12.2
selenium==4.15.2

# API Documentation
jinja2==3.1.2

# Cache
hiredis==2.2.3

# Time Series Analysis (for trend analysis)
statsmodels==0.14.0

# Text Processing
nltk==3.8.1
spacy==3.7.2

# Development Server
watchfiles==0.21.0

# Phase 2 Dependencies - Docker Sandbox
docker>=6.1.0
aiofiles>=23.0.0

# Phase 2 Dependencies - Google Colab Compatibility
psutil>=5.9.0
jupyter>=1.0.0
ipywidgets>=8.0.0
google-colab>=1.0.0

# Additional Phase 2 utilities
gitpython>=3.1.40
"""

# Write updated requirements
with open('/home/z/my-project/backend/requirements.txt', 'w') as f:
    f.write(existing_requirements)

print("✅ Updated requirements.txt with Phase 2 dependencies")
# Sovereign AI Arsenal

A modular AI intelligence platform for discovering, analyzing, and monitoring AI-related repositories. Built with FastAPI, PostgreSQL, and advanced AI analytics.

## 🚀 Features

### Core Capabilities
- **Intelligent Repository Discovery**: Automated GitHub API integration with smart filtering
- **Multi-dimensional Analysis**: Comprehensive repository evaluation across technical, business, and innovation metrics
- **Advanced Classification**: AI-powered categorization and tagging system
- **Trend Analysis**: Sophisticated growth pattern analysis and predictions
- **Vector Search**: Semantic search capabilities using embeddings
- **Real-time Monitoring**: Continuous tracking of repository metrics and trends

### Technical Highlights
- **Modular Architecture**: Clean, scalable design with separation of concerns
- **Operational Foundations**: Structured logging, health checks, and monitoring integrations
- **High Performance**: Async operations, caching, and optimized database queries
- **Containerized**: Full Docker support with orchestration
- **API-First**: RESTful API with comprehensive documentation

## 📋 Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- GitHub API Token
- OpenAI API Key (for LLM analysis)

## 🛠️ Installation

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd sovereign-ai-arsenal
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Generate three different secrets with: openssl rand -hex 32
# Set POSTGRES_ADMIN_PASSWORD, DB_PASSWORD, and GRAFANA_ADMIN_PASSWORD
```

3. **Start the platform**
```bash
docker compose up -d
```

4. **Access the services**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Grafana Dashboard: http://localhost:3000 (admin; password from GRAFANA_ADMIN_PASSWORD)
- PostgreSQL: localhost:5432 (local development access only)
- Redis is internal to the Compose network and is not published on the host
- Prometheus: http://localhost:9090

### Manual Installation

1. **Install system dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv postgresql-15 redis-server

# macOS
brew install python@3.11 postgresql@15 redis
```

2. **Set up Python environment**
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure database**
```bash
# Create PostgreSQL database
createdb sovereign_ai_arsenal

# Run migrations
python -m alembic upgrade head
```

4. **Configure environment**
```bash
cp ../.env.example ../.env
# Set POSTGRES_ADMIN_PASSWORD, DB_PASSWORD, and GRAFANA_ADMIN_PASSWORD; keep secrets out of Git
set -a && source ../.env && set +a
```

5. **Start the application**
```bash
cd .. && PYTHONPATH=. uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## ⚙️ Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sovereign_ai_arsenal
DB_USER=app_user
DB_PASSWORD=<unique-app-database-secret>
POSTGRES_ADMIN_PASSWORD=<unique-postgres-admin-secret>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# APIs
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Application
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
```

### Configuration File (config.yaml)

The platform uses config.yaml for non-secret defaults. Database credentials are supplied only through environment variables. The Compose bootstrap creates a separate, non-superuser app_user role for the API.

```yaml
app_name: "Sovereign AI Arsenal"
version: "1.0.0"

database:
  host: localhost
  port: 5432
  name: sovereign_ai_arsenal
  user: app_user
  # DB_PASSWORD is supplied through the environment; never commit credentials.
  pool_size: 10
  max_overflow: 20

github:
  api_url: "https://api.github.com"
  token: ${GITHUB_TOKEN}
  rate_limit:
    requests_per_hour: 5000
    retry_after: 60

ai_models:
  embedding_model: "all-MiniLM-L6-v2"
  llm_model: "gpt-4"
  max_tokens: 4000
  temperature: 0.1

scoring:
  weights:
    stars: 0.3
    forks: 0.2
    contributors: 0.2
    commit_frequency: 0.15
    trend_growth: 0.15
  thresholds:
    minimum_stars: 30
    trending_growth_rate: 0.1
    active_contributors: 3
```

## 📚 API Documentation

### Core Endpoints

#### Repository Management
- `GET /api/v1/repositories` - List repositories with filtering
- `GET /api/v1/repositories/{id}` - Get repository details
- `POST /api/v1/discover` - Discover new repositories
- `POST /api/v1/repositories/{id}/analyze` - Analyze repository

#### Search & Discovery
- `GET /api/v1/search` - Search repositories
- `GET /api/v1/trending` - Get trending repositories
- `GET /api/v1/categories` - List categories

#### Analytics
- `GET /api/v1/statistics` - Platform statistics
- `GET /metrics` - Application metrics

### Example API Usage

```python
import httpx

# Discover repositories
async def discover_repos():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/discover",
            params={"queries": ["machine learning", "deep learning"], "max_repos_per_query": 50}
        )
        return response.json()

# Search repositories
async def search_repos(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/search",
            params={"q": query, "search_type": "semantic"}
        )
        return response.json()
```

## 🏗️ Architecture

### Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── api/
│   └── routes.py         # API route definitions
├── core/
│   ├── discovery.py      # GitHub discovery engine
│   ├── evaluator.py      # Repository evaluation
│   ├── classifier.py     # AI classification
│   ├── scorer.py         # Comprehensive scoring
│   ├── trend_engine.py   # Trend analysis
│   └── llm_analyzer.py  # LLM-powered analysis
├── database/
│   ├── db.py            # Database configuration
│   ├── models.py        # SQLAlchemy models
│   └── vector_store.py  # Vector embeddings
└── logging_config.py    # Logging configuration
```

### Core Components

1. **Discovery Engine**: Automated GitHub repository discovery with intelligent filtering
2. **Evaluator**: Multi-dimensional repository analysis and scoring
3. **Classifier**: AI-powered categorization and tagging
4. **Scorer**: Comprehensive scoring system with weighted metrics
5. **Trend Engine**: Advanced trend analysis and predictions
6. **LLM Analyzer**: Deep language model analysis for insights
7. **Vector Store**: Semantic search using embeddings

### Database Schema

The platform uses PostgreSQL with the following main entities:

- **Repository**: Core repository information
- **RepositoryMetrics**: Detailed metrics and analytics
- **Classification**: AI-powered categories and tags
- **Trend**: Historical trend data
- **Contributor**: Contributor information
- **Commit**: Commit history and analysis

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding New Features

1. **Create new core module** in `backend/core/`
2. **Define database models** in `backend/database/models.py`
3. **Add API endpoints** in `backend/api/routes.py`
4. **Write tests** for new functionality
5. **Update documentation**

## 📊 Monitoring

### Metrics Collection

The platform includes comprehensive monitoring:

- **Application Metrics**: Request times, error rates, user activity
- **Database Metrics**: Query performance, connection pool usage
- **Business Metrics**: Repository counts, analysis success rates
- **System Metrics**: CPU, memory, disk usage

### Grafana Dashboards

Pre-configured dashboards include:

- **Platform Overview**: High-level system health
- **API Performance**: Request metrics and error tracking
- **Database Performance**: Query analysis and connection monitoring
- **Business Analytics**: Repository discovery and analysis metrics

### Alerting

Configure alerts in Prometheus for:

- High error rates
- Slow database queries
- API downtime
- Resource exhaustion

## 🔒 Security

### Authentication

Authentication is not yet enforced at the API boundary. Do not expose the API publicly until authentication and authorization are implemented and tested. The following mechanisms are planned, not currently verified:

- API Keys (for programmatic access)
- JWT Tokens (for web applications)
- OAuth2 (for third-party integrations)

### Rate Limiting

Built-in rate limiting to prevent abuse:

```yaml
api:
  rate_limiting:
    requests_per_minute: 100
    burst_size: 20
```

### Data Protection

- Keep database and monitoring ports on loopback unless a reviewed deployment requires otherwise
- Supply credentials through environment variables or a secret manager
- Terminate public traffic through a configured TLS reverse proxy
- Add encryption-at-rest and audit controls before production use

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Production environment variables
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export DEBUG=false
```

2. **Database Setup**
```bash
# Create production database
createdb sovereign_ai_arsenal_prod

# Run migrations with production settings
alembic upgrade head
```

3. **Application Deployment**
```bash
# Build and deploy with Docker
docker compose -f docker-compose.prod.yml up -d

# Or manual deployment
PYTHONPATH=. uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 4
```

### Scaling

- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database Scaling**: Read replicas and connection pooling
- **Cache Scaling**: Redis cluster for high availability
- **Storage Scaling**: Distributed file system for vector data

### Backup Strategy

- **Database Backups**: Automated daily backups with point-in-time recovery
- **Vector Store Backups**: Regular snapshots of embedding data
- **Configuration Backups**: Version-controlled configuration management
- **Disaster Recovery**: Multi-region deployment for critical services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use meaningful commit messages
- Ensure CI/CD passes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full documentation](https://docs.sovereign-ai-arsenal.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/sovereign-ai-arsenal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/sovereign-ai-arsenal/discussions)
- **Email**: support@sovereign-ai-arsenal.com

## 🎯 Roadmap

### Version 1.1
- [ ] Enhanced ML model recommendations
- [ ] Real-time WebSocket updates
- [ ] Advanced filtering options
- [ ] Export functionality

### Version 1.2
- [ ] Multi-language repository support
- [ ] Custom scoring algorithms
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard

### Version 2.0
- [ ] Machine learning model hosting
- [ ] Automated repository analysis
- [ ] Integration with more platforms
- [ ] Advanced AI insights

---

**Built with ❤️ by the Sovereign AI Arsenal team**

### Existing database volumes

The role-bootstrap script runs only when PostgreSQL initializes an empty data volume. If this stack has already been started with an older volume, **do not delete the volume** to apply the new role model. Back up the database and perform a reviewed role/password migration against the existing instance first.

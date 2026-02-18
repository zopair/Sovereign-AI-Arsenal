from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    html_url = Column(String(500), nullable=False)
    clone_url = Column(String(500))
    ssh_url = Column(String(500))
    language = Column(String(100), index=True)
    size = Column(Integer)
    stargazers_count = Column(Integer, default=0, index=True)
    watchers_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    subscribers_count = Column(Integer, default=0)
    license = Column(String(100))
    is_fork = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    visibility = Column(String(20), default="public")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False, index=True)
    pushed_at = Column(DateTime, nullable=False)
    default_branch = Column(String(100))
    topics = Column(JSON)
    score = Column(Float, default=0.0, index=True)
    trend_score = Column(Float, default=0.0, index=True)
    ai_relevance_score = Column(Float, default=0.0, index=True)
    last_analyzed = Column(DateTime)
    embedding_id = Column(String(255), index=True)
    
    # Relationships
    metrics = relationship("RepositoryMetrics", back_populates="repository", cascade="all, delete-orphan")
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    contributors = relationship("Contributor", back_populates="repository", cascade="all, delete-orphan")
    classifications = relationship("Classification", back_populates="repository", cascade="all, delete-orphan")


class RepositoryMetrics(Base):
    __tablename__ = "repository_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    stars_growth_rate = Column(Float, default=0.0)
    forks_growth_rate = Column(Float, default=0.0)
    commit_frequency = Column(Float, default=0.0)
    contributor_activity = Column(Float, default=0.0)
    issue_resolution_rate = Column(Float, default=0.0)
    code_churn = Column(Float, default=0.0)
    bus_factor = Column(Integer, default=1)
    technical_debt = Column(Float, default=0.0)
    community_health = Column(Float, default=0.0)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="metrics")


class Contributor(Base):
    __tablename__ = "contributors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    github_id = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    contributions = Column(Integer, default=0)
    first_commit_date = Column(DateTime)
    last_commit_date = Column(DateTime)
    total_commits = Column(Integer, default=0)
    total_additions = Column(Integer, default=0)
    total_deletions = Column(Integer, default=0)
    is_core_contributor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="contributors")


class Commit(Base):
    __tablename__ = "commits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    sha = Column(String(40), nullable=False)
    message = Column(Text)
    author_name = Column(String(255))
    author_email = Column(String(255))
    author_date = Column(DateTime)
    committer_name = Column(String(255))
    committer_email = Column(String(255))
    committer_date = Column(DateTime)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    merge = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="commits")


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    confidence = Column(Float, default=0.0)
    tags = Column(JSON)
    reasoning = Column(Text)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="classifications")


class Trend(Base):
    __tablename__ = "trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    contributors = Column(Integer, default=0)
    commits = Column(Integer, default=0)
    issues_opened = Column(Integer, default=0)
    issues_closed = Column(Integer, default=0)
    pull_requests_opened = Column(Integer, default=0)
    pull_requests_merged = Column(Integer, default=0)
    weekly_growth_rate = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    
    # Relationships
    repository = relationship("Repository")


class AISearchQuery(Base):
    __tablename__ = "ai_search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    query_type = Column(String(50), default="search")
    filters = Column(JSON)
    results_count = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    user_ip = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    tags = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
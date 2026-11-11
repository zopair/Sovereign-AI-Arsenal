from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timedelta

from ..database.db import get_db, db as database
from ..database.models import Repository, Classification, Trend
from ..core.discovery import GitHubDiscoveryEngine
from ..core.evaluator import RepositoryEvaluator
from ..core.classifier import RepositoryClassifier
from ..core.scorer import RepositoryScorer
from ..core.trend_engine import TrendAnalysisEngine
from ..core.llm_analyzer import LLMAnalyzer
from ..database.vector_store import get_vector_store

logger = logging.getLogger(__name__)
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"

router = APIRouter(prefix="/api/v1", tags=["repositories"])

# Initialize core components
def get_discovery_engine():
    import yaml
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return GitHubDiscoveryEngine(config.get('github', {}))

def get_evaluator():
    import yaml
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return RepositoryEvaluator(config)

def get_classifier():
    import yaml
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return RepositoryClassifier(config)

def get_scorer():
    import yaml
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return RepositoryScorer(config)

def get_trend_engine():
    import yaml
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return TrendAnalysisEngine(config)

def get_llm_analyzer():
    import yaml
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return LLMAnalyzer(config)

@router.get("/repositories", response_model=List[Dict[str, Any]])
async def get_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("overall_score", regex="^(overall_score|stars|forks|updated_at|created_at)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    category: Optional[str] = Query(None),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """Get repositories with filtering and sorting"""
    try:
        query = db.query(Repository)
        
        # Apply filters
        if category:
            query = query.join(Classification).filter(Classification.category == category)
        
        if min_score > 0:
            query = query.filter(Repository.score >= min_score)
        
        # Apply sorting
        if order == "desc":
            query = query.order_by(getattr(Repository, sort_by).desc())
        else:
            query = query.order_by(getattr(Repository, sort_by).asc())
        
        # Apply pagination
        repositories = query.offset(skip).limit(limit).all()
        
        # Convert to dict format
        result = []
        for repo in repositories:
            repo_dict = {
                'id': str(repo.id),
                'github_id': repo.github_id,
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'html_url': repo.html_url,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat(),
                'score': repo.score,
                'trend_score': repo.trend_score,
                'ai_relevance_score': repo.ai_relevance_score,
                'topics': repo.topics,
                'license': repo.license and repo.license.get('name') if isinstance(repo.license, dict) else repo.license
            }
            result.append(repo_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting repositories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/repositories/{repo_id}", response_model=Dict[str, Any])
async def get_repository(repo_id: str, db: Session = Depends(get_db)):
    """Get detailed repository information"""
    try:
        repository = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get related data
        classifications = db.query(Classification).filter(Classification.repository_id == repo_id).all()
        trends = db.query(Trend).filter(Trend.repository_id == repo_id).order_by(Trend.date.desc()).limit(52).all()
        
        # Build response
        repo_data = {
            'id': str(repository.id),
            'github_id': repository.github_id,
            'name': repository.name,
            'full_name': repository.full_name,
            'description': repository.description,
            'html_url': repository.html_url,
            'clone_url': repository.clone_url,
            'language': repository.language,
            'size': repository.size,
            'stars': repository.stargazers_count,
            'forks': repository.forks_count,
            'open_issues': repository.open_issues_count,
            'watchers': repository.watchers_count,
            'subscribers': repository.subscribers_count,
            'created_at': repository.created_at.isoformat(),
            'updated_at': repository.updated_at.isoformat(),
            'pushed_at': repository.pushed_at.isoformat(),
            'default_branch': repository.default_branch,
            'topics': repository.topics,
            'license': repository.license,
            'is_fork': repository.is_fork,
            'is_archived': repository.is_archived,
            'score': repository.score,
            'trend_score': repository.trend_score,
            'ai_relevance_score': repository.ai_relevance_score,
            'last_analyzed': repository.last_analyzed.isoformat() if repository.last_analyzed else None,
            'classifications': [
                {
                    'category': c.category,
                    'confidence': c.confidence,
                    'subcategory': c.subcategory,
                    'tags': c.tags,
                    'reasoning': c.reasoning
                } for c in classifications
            ],
            'trends': [
                {
                    'date': t.date.isoformat(),
                    'stars': t.stars,
                    'forks': t.forks,
                    'contributors': t.contributors,
                    'commits': t.commits,
                    'weekly_growth_rate': t.weekly_growth_rate,
                    'trend_score': t.trend_score
                } for t in trends
            ]
        }
        
        return repo_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting repository {repo_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/discover")
async def discover_repositories(
    background_tasks: BackgroundTasks,
    queries: Optional[List[str]] = Query(None),
    max_repos_per_query: int = Query(100, ge=1, le=500),
    auto_analyze: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Discover new AI repositories"""
    try:
        discovery_engine = get_discovery_engine()
        
        # Start discovery in background
        background_tasks.add_task(
            discover_and_analyze_repositories,
            discovery_engine,
            queries,
            max_repos_per_query,
            auto_analyze,
        )
        
        return {"message": "Repository discovery started", "status": "processing"}
        
    except Exception as e:
        logger.error(f"Error starting repository discovery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/repositories/{repo_id}/analyze")
async def analyze_repository(
    repo_id: str,
    background_tasks: BackgroundTasks,
    force_reanalyze: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Trigger comprehensive analysis of a repository"""
    try:
        repository = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repository:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Start analysis in background
        background_tasks.add_task(
            perform_comprehensive_analysis,
            str(repository.id),
            force_reanalyze,
        )
        
        return {"message": "Repository analysis started", "status": "processing"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting repository analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search")
async def search_repositories(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search_type: str = Query("semantic", regex="^(semantic|keyword|hybrid)$"),
    db: Session = Depends(get_db)
):
    """Search repositories using semantic or keyword search"""
    try:
        if search_type == "semantic":
            return await semantic_search(q, skip, limit, db)
        elif search_type == "keyword":
            return await keyword_search(q, skip, limit, db)
        else:  # hybrid
            semantic_results = await semantic_search(q, skip, limit//2, db)
            keyword_results = await keyword_search(q, skip, limit//2, db)
            
            # Combine and deduplicate results
            combined = {}
            for result in semantic_results + keyword_results:
                repo_id = result['id']
                if repo_id not in combined or result.get('relevance_score', 0) > combined[repo_id].get('relevance_score', 0):
                    combined[repo_id] = result
            
            return list(combined.values())[:limit]
        
    except Exception as e:
        logger.error(f"Error searching repositories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def semantic_search(query: str, skip: int, limit: int, db: Session):
    """Semantic search using vector embeddings"""
    try:
        vector_store = get_vector_store()
        search_results = vector_store.search_similar_repositories(query, limit + skip)
        
        # Get repository details
        repo_ids = [result['id'] for result in search_results[skip:skip+limit]]
        repositories = db.query(Repository).filter(Repository.id.in_(repo_ids)).all()
        
        # Build response
        result = []
        repo_map = {str(repo.id): repo for repo in repositories}
        
        for search_result in search_results[skip:skip+limit]:
            repo_id = search_result['id']
            if repo_id in repo_map:
                repo = repo_map[repo_id]
                result.append({
                    'id': str(repo.id),
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'language': repo.language,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'score': repo.score,
                    'relevance_score': search_result['similarity_score'],
                    'updated_at': repo.updated_at.isoformat()
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return []

async def keyword_search(query: str, skip: int, limit: int, db: Session):
    """Keyword search in database"""
    try:
        search_pattern = f"%{query.lower()}%"
        
        repositories = db.query(Repository).filter(
            (Repository.name.ilike(search_pattern)) |
            (Repository.description.ilike(search_pattern)) |
            (Repository.language.ilike(search_pattern))
        ).offset(skip).limit(limit).all()
        
        result = []
        for repo in repositories:
            result.append({
                'id': str(repo.id),
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'score': repo.score,
                'relevance_score': 0.8,  # Default relevance for keyword matches
                'updated_at': repo.updated_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in keyword search: {e}")
        return []

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all available categories with repository counts"""
    try:
        categories = db.query(
            Classification.category,
            db.func.count(Classification.id).label('count')
        ).group_by(Classification.category).order_by(db.func.count(Classification.id).desc()).all()
        
        result = [
            {'category': category, 'repository_count': count}
            for category, count in categories
        ]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trending")
async def get_trending_repositories(
    time_period: str = Query("week", regex="^(day|week|month|year)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get trending repositories"""
    try:
        # Calculate date threshold
        from datetime import timedelta
        if time_period == "day":
            threshold = datetime.utcnow() - timedelta(days=1)
        elif time_period == "week":
            threshold = datetime.utcnow() - timedelta(weeks=1)
        elif time_period == "month":
            threshold = datetime.utcnow() - timedelta(days=30)
        else:  # year
            threshold = datetime.utcnow() - timedelta(days=365)
        
        repositories = db.query(Repository).filter(
            Repository.updated_at >= threshold,
            Repository.trend_score > 0.1
        ).order_by(Repository.trend_score.desc()).limit(limit).all()
        
        result = []
        for repo in repositories:
            result.append({
                'id': str(repo.id),
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'trend_score': repo.trend_score,
                'overall_score': repo.score,
                'updated_at': repo.updated_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting trending repositories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get platform statistics"""
    try:
        total_repos = db.query(Repository).count()
        total_stars = db.query(db.func.sum(Repository.stargazers_count)).scalar() or 0
        total_forks = db.query(db.func.sum(Repository.forks_count)).scalar() or 0
        
        # Language distribution
        languages = db.query(
            Repository.language,
            db.func.count(Repository.id).label('count')
        ).filter(Repository.language.isnot(None)).group_by(Repository.language).order_by(db.func.count(Repository.id).desc()).limit(10).all()
        
        # Category distribution
        categories = db.query(
            Classification.category,
            db.func.count(Classification.id).label('count')
        ).group_by(Classification.category).order_by(db.func.count(Classification.id).desc()).limit(10).all()
        
        # Recent activity
        recent_repos = db.query(Repository).filter(
            Repository.updated_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return {
            'total_repositories': total_repos,
            'total_stars': total_stars,
            'total_forks': total_forks,
            'recent_activity': recent_repos,
            'top_languages': [
                {'language': lang, 'count': count} for lang, count in languages
            ],
            'top_categories': [
                {'category': cat, 'count': count} for cat, count in categories
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Background task functions
async def discover_and_analyze_repositories(
    discovery_engine: GitHubDiscoveryEngine,
    queries: Optional[List[str]],
    max_repos_per_query: int,
    auto_analyze: bool,
):
    """Discover repositories; each unit of DB work owns a short-lived session."""
    try:
        repositories = await discovery_engine.discover_ai_repositories(queries, max_repos_per_query)

        for repo_data in repositories:
            try:
                with database.get_session() as session:
                    repository = session.query(Repository).filter(
                        Repository.github_id == repo_data["id"]
                    ).first()

                    if repository:
                        repository.stargazers_count = repo_data.get("stargazers_count", repository.stargazers_count)
                        repository.forks_count = repo_data.get("forks_count", repository.forks_count)
                        repository.open_issues_count = repo_data.get("open_issues_count", repository.open_issues_count)
                        repository.updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))
                        repository.pushed_at = datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00"))
                        repository.topics = repo_data.get("topics", [])
                    else:
                        repository = Repository(
                            github_id=repo_data["id"],
                            name=repo_data["name"],
                            full_name=repo_data["full_name"],
                            description=repo_data.get("description"),
                            html_url=repo_data["html_url"],
                            clone_url=repo_data.get("clone_url"),
                            language=repo_data.get("language"),
                            size=repo_data.get("size"),
                            stargazers_count=repo_data.get("stargazers_count", 0),
                            forks_count=repo_data.get("forks_count", 0),
                            open_issues_count=repo_data.get("open_issues_count", 0),
                            watchers_count=repo_data.get("watchers_count", 0),
                            subscribers_count=repo_data.get("subscribers_count", 0),
                            license=repo_data.get("license"),
                            is_fork=repo_data.get("fork", False),
                            is_archived=repo_data.get("archived", False),
                            created_at=datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00")),
                            pushed_at=datetime.fromisoformat(repo_data["pushed_at"].replace("Z", "+00:00")),
                            default_branch=repo_data.get("default_branch"),
                            topics=repo_data.get("topics", []),
                        )
                        session.add(repository)
                        session.flush()

                    repository_id = str(repository.id)
                    session.commit()

                if auto_analyze:
                    await perform_comprehensive_analysis(repository_id, False)

            except Exception:
                logger.exception("Error processing discovered repository %s", repo_data.get("full_name", "unknown"))
                continue

        logger.info("Processed %s discovered repositories", len(repositories))

    except Exception:
        logger.exception("Repository discovery background task failed")

async def perform_comprehensive_analysis(repo_id: str, force_reanalyze: bool):
    """Analyze a repository without retaining a DB session during network/model work."""
    try:
        with database.get_session() as session:
            repository = session.query(Repository).filter(Repository.id == repo_id).first()
            if not repository:
                return

            if not force_reanalyze and repository.last_analyzed:
                if (datetime.utcnow() - repository.last_analyzed).days < 1:
                    return

            repository_snapshot = {
                "id": repository.github_id,
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "language": repository.language,
                "stargazers_count": repository.stargazers_count,
                "forks_count": repository.forks_count,
                "open_issues_count": repository.open_issues_count,
                "topics": repository.topics,
                "license": repository.license,
                "created_at": repository.created_at.isoformat(),
                "updated_at": repository.updated_at.isoformat(),
            }

        discovery_engine = get_discovery_engine()
        repo_metrics = await discovery_engine.update_repository_metrics(SimpleNamespace(**repository_snapshot))
        repo_data = {**repository_snapshot, "metrics": repo_metrics}

        readme = await discovery_engine.get_repository_readme(repository_snapshot["full_name"])
        if readme:
            repo_data["readme_content"] = readme

        evaluation = get_evaluator().evaluate_repository(repo_data, repo_metrics)
        classifications = get_classifier().classify_repository(repo_data)
        scores = get_scorer().calculate_composite_score(repo_data, repo_metrics)
        trend_analysis = get_trend_engine().analyze_repository_trends(repo_data)

        with database.get_session() as session:
            repository = session.query(Repository).filter(Repository.id == repo_id).first()
            if not repository:
                return

            repository.score = scores.get("overall_score", 0.0)
            repository.trend_score = scores.get("trend_score", 0.0)
            repository.ai_relevance_score = evaluation.get("ai_relevance_score", 0.0)
            repository.last_analyzed = datetime.utcnow()

            existing_classifications = session.query(Classification).filter(
                Classification.repository_id == repo_id
            ).all()
            for existing in existing_classifications:
                session.delete(existing)

            for item in classifications:
                session.add(Classification(
                    repository_id=repo_id,
                    category=item["category"],
                    subcategory=item.get("subcategory"),
                    confidence=item["confidence"],
                    tags=item.get("tags"),
                    reasoning=item.get("reasoning"),
                    model_version=item.get("model_version"),
                ))

            if trend_analysis:
                session.add(Trend(
                    repository_id=repo_id,
                    date=datetime.utcnow(),
                    stars=repository.stargazers_count,
                    forks=repository.forks_count,
                    contributors=repo_metrics.get("contributors_count", 0),
                    commits=repo_metrics.get("commits_30_days", 0),
                    weekly_growth_rate=repo_metrics.get("weekly_growth_rate", 0.0),
                    trend_score=trend_analysis.get("trend_metrics", {}).get("trend_strength", 0.0),
                ))

            session.commit()

        if readme:
            get_vector_store().add_repository_embedding(
                repo_id,
                readme,
                {
                    "name": repository_snapshot["name"],
                    "full_name": repository_snapshot["full_name"],
                    "language": repository_snapshot["language"],
                    "stars": repository_snapshot["stargazers_count"],
                    "updated_at": repository_snapshot["updated_at"],
                },
            )

        logger.info("Completed analysis for repository %s", repository_snapshot["full_name"])

    except Exception:
        logger.exception("Repository analysis background task failed for %s", repo_id)

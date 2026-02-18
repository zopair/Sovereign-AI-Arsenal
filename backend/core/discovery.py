import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from ..database.models import Repository
from ..database.db import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class GitHubDiscoveryEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.github_api_url = config.get('api_url', 'https://api.github.com')
        self.token = config.get('token') or os.getenv('GITHUB_TOKEN')
        self.rate_limit = config.get('rate_limit', {})
        self.session = None
        
    async def __aenter__(self):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.token}' if self.token else None,
            'User-Agent': 'Sovereign-AI-Arsenal/1.0'
        }
        headers = {k: v for k, v in headers.items() if v is not None}
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_repositories(self, 
                                query: str = "artificial intelligence machine learning",
                                sort: str = "stars",
                                order: str = "desc",
                                per_page: int = 100,
                                page: int = 1) -> Dict[str, Any]:
        """Search GitHub repositories with AI-related filters"""
        try:
            url = f"{self.github_api_url}/search/repositories"
            params = {
                'q': query,
                'sort': sort,
                'order': order,
                'per_page': per_page,
                'page': page
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Found {data['total_count']} repositories for query: {query}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"GitHub API error: {response.status} - {error_text}")
                    raise Exception(f"GitHub API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to search repositories: {e}")
            raise
    
    async def get_repository_details(self, repo_full_name: str) -> Dict[str, Any]:
        """Get detailed repository information"""
        try:
            url = f"{self.github_api_url}/repos/{repo_full_name}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get repository details: {response.status} - {error_text}")
                    raise Exception(f"Failed to get repository details: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to get repository details: {e}")
            raise
    
    async def get_repository_readme(self, repo_full_name: str) -> Optional[str]:
        """Get repository README content"""
        try:
            url = f"{self.github_api_url}/repos/{repo_full_name}/readme"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Get README content (it's base64 encoded)
                    if 'download_url' in data:
                        async with self.session.get(data['download_url']) as readme_response:
                            if readme_response.status == 200:
                                return await readme_response.text()
                    return None
                elif response.status == 404:
                    logger.info(f"No README found for {repo_full_name}")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get README: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get repository README: {e}")
            return None
    
    async def get_repository_contributors(self, repo_full_name: str) -> List[Dict[str, Any]]:
        """Get repository contributors"""
        try:
            url = f"{self.github_api_url}/repos/{repo_full_name}/contributors"
            contributors = []
            page = 1
            per_page = 100
            
            while True:
                params = {'per_page': per_page, 'page': page}
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            break
                        contributors.extend(data)
                        page += 1
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get contributors: {response.status} - {error_text}")
                        break
                        
            return contributors
            
        except Exception as e:
            logger.error(f"Failed to get repository contributors: {e}")
            return []
    
    async def get_repository_commits(self, 
                                   repo_full_name: str, 
                                   since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get repository commits"""
        try:
            url = f"{self.github_api_url}/repos/{repo_full_name}/commits"
            commits = []
            page = 1
            per_page = 100
            
            params = {'per_page': per_page, 'page': page}
            if since:
                params['since'] = since.isoformat()
            
            while True:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data:
                            break
                        commits.extend(data)
                        page += 1
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get commits: {response.status} - {error_text}")
                        break
                        
            return commits
            
        except Exception as e:
            logger.error(f"Failed to get repository commits: {e}")
            return []
    
    def _filter_repository(self, repo_data: Dict[str, Any]) -> bool:
        """Apply filters to repository data"""
        try:
            # Minimum stars filter
            min_stars = self.config.get('minimum_stars', 30)
            if repo_data.get('stargazers_count', 0) < min_stars:
                return False
            
            # Not archived filter
            if repo_data.get('archived', False):
                return False
            
            # Updated in last 30 days filter
            updated_at = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            if updated_at < thirty_days_ago:
                return False
            
            # AI relevance filter (basic check)
            ai_keywords = [
                'artificial intelligence', 'machine learning', 'deep learning',
                'neural network', 'tensorflow', 'pytorch', 'ai', 'ml', 'nlp',
                'computer vision', 'reinforcement learning', 'gpt', 'llm',
                'transformer', 'bert', 'chatbot', 'automation'
            ]
            
            repo_text = f"{repo_data.get('name', '')} {repo_data.get('description', '')} {' '.join(repo_data.get('topics', []))}"
            repo_text = repo_text.lower()
            
            if not any(keyword in repo_text for keyword in ai_keywords):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error filtering repository: {e}")
            return False
    
    async def discover_ai_repositories(self, 
                                     queries: List[str] = None,
                                     max_repos_per_query: int = 100) -> List[Dict[str, Any]]:
        """Discover AI-related repositories"""
        if queries is None:
            queries = [
                "artificial intelligence machine learning",
                "deep learning neural network",
                "computer vision image processing",
                "natural language processing nlp",
                "reinforcement learning ai",
                "tensorflow pytorch machine learning",
                "large language model llm",
                "generative ai gpt"
            ]
        
        all_repositories = []
        seen_repos = set()
        
        async with self:
            for query in queries:
                try:
                    # Search for repositories
                    search_results = await self.search_repositories(
                        query=query,
                        per_page=max_repos_per_query
                    )
                    
                    # Filter and process repositories
                    for repo_data in search_results.get('items', []):
                        repo_id = repo_data['id']
                        
                        if repo_id in seen_repos:
                            continue
                        
                        if not self._filter_repository(repo_data):
                            continue
                        
                        # Get additional details
                        try:
                            readme = await self.get_repository_readme(repo_data['full_name'])
                            contributors = await self.get_repository_contributors(repo_data['full_name'])
                            
                            # Enhance repository data
                            repo_data['readme_content'] = readme
                            repo_data['contributors_count'] = len(contributors)
                            repo_data['top_contributors'] = contributors[:10]
                            
                            all_repositories.append(repo_data)
                            seen_repos.add(repo_id)
                            
                        except Exception as e:
                            logger.warning(f"Failed to get additional details for {repo_data['full_name']}: {e}")
                            # Still add the repository even if we can't get all details
                            all_repositories.append(repo_data)
                            seen_repos.add(repo_id)
                    
                    # Rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing query '{query}': {e}")
                    continue
        
        logger.info(f"Discovered {len(all_repositories)} AI repositories")
        return all_repositories
    
    async def update_repository_metrics(self, 
                                      repository: Repository) -> Dict[str, Any]:
        """Update repository metrics with fresh data"""
        try:
            async with self:
                # Get fresh repository data
                repo_data = await self.get_repository_details(repository.full_name)
                
                # Get recent commits
                since = datetime.utcnow() - timedelta(days=30)
                commits = await self.get_repository_commits(repository.full_name, since)
                
                # Get contributors
                contributors = await self.get_repository_contributors(repository.full_name)
                
                # Calculate metrics
                metrics = {
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'open_issues': repo_data.get('open_issues_count', 0),
                    'contributors_count': len(contributors),
                    'commits_30_days': len(commits),
                    'last_commit_date': None,
                    'commit_frequency': 0.0,
                    'contributor_activity': 0.0
                }
                
                # Calculate commit frequency
                if commits:
                    last_commit = datetime.fromisoformat(commits[0]['commit']['committer']['date'].replace('Z', '+00:00'))
                    metrics['last_commit_date'] = last_commit
                    metrics['commit_frequency'] = len(commits) / 30.0  # commits per day
                
                # Calculate contributor activity
                if contributors:
                    active_contributors = sum(1 for c in contributors if c.get('contributions', 0) > 0)
                    metrics['contributor_activity'] = active_contributors / len(contributors)
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to update repository metrics: {e}")
            return {}
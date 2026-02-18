import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from ..database.models import Repository, RepositoryMetrics
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class RepositoryEvaluator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scoring_weights = config.get('scoring', {}).get('weights', {
            'stars': 0.3,
            'forks': 0.2,
            'contributors': 0.2,
            'commit_frequency': 0.15,
            'trend_growth': 0.15
        })
        self.thresholds = config.get('scoring', {}).get('thresholds', {
            'minimum_stars': 30,
            'trending_growth_rate': 0.1,
            'active_contributors': 3
        })
    
    def evaluate_repository(self, 
                           repo_data: Dict[str, Any], 
                           metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate a repository and calculate various scores"""
        try:
            evaluation = {
                'repo_id': repo_data.get('id'),
                'repo_name': repo_data.get('full_name'),
                'overall_score': 0.0,
                'component_scores': {},
                'ai_relevance_score': 0.0,
                'quality_score': 0.0,
                'popularity_score': 0.0,
                'activity_score': 0.0,
                'trend_score': 0.0,
                'evaluation_date': datetime.utcnow().isoformat(),
                'recommendations': []
            }
            
            # Calculate component scores
            evaluation['component_scores'] = self._calculate_component_scores(repo_data, metrics)
            
            # Calculate specialized scores
            evaluation['ai_relevance_score'] = self._calculate_ai_relevance_score(repo_data)
            evaluation['quality_score'] = self._calculate_quality_score(repo_data, metrics)
            evaluation['popularity_score'] = self._calculate_popularity_score(repo_data)
            evaluation['activity_score'] = self._calculate_activity_score(repo_data, metrics)
            evaluation['trend_score'] = self._calculate_trend_score(repo_data, metrics)
            
            # Calculate overall score
            evaluation['overall_score'] = self._calculate_overall_score(evaluation)
            
            # Generate recommendations
            evaluation['recommendations'] = self._generate_recommendations(evaluation, repo_data)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Failed to evaluate repository: {e}")
            return {}
    
    def _calculate_component_scores(self, 
                                  repo_data: Dict[str, Any], 
                                  metrics: Dict[str, Any] = None) -> Dict[str, float]:
        """Calculate individual component scores"""
        scores = {}
        
        try:
            # Stars score (logarithmic scaling)
            stars = repo_data.get('stargazers_count', 0)
            scores['stars'] = np.log10(max(stars, 1)) / 6.0  # Normalize to 0-1
            
            # Forks score
            forks = repo_data.get('forks_count', 0)
            scores['forks'] = np.log10(max(forks, 1)) / 5.0
            
            # Contributors score
            contributors = metrics.get('contributors_count', 0) if metrics else 0
            scores['contributors'] = min(contributors / 100.0, 1.0)
            
            # Commit frequency score
            commit_frequency = metrics.get('commit_frequency', 0) if metrics else 0
            scores['commit_frequency'] = min(commit_frequency / 10.0, 1.0)  # 10 commits/day = 1.0
            
            # Trend growth score
            trend_growth = metrics.get('stars_growth_rate', 0) if metrics else 0
            scores['trend_growth'] = min(abs(trend_growth) / 0.5, 1.0)  # 50% growth = 1.0
            
            # Issue resolution score
            issues_open = repo_data.get('open_issues_count', 0)
            issues_closed = metrics.get('issues_closed', 0) if metrics else 0
            total_issues = issues_open + issues_closed
            if total_issues > 0:
                scores['issue_resolution'] = issues_closed / total_issues
            else:
                scores['issue_resolution'] = 0.5  # Neutral score
            
            # Code health score
            scores['code_health'] = self._calculate_code_health_score(repo_data, metrics)
            
        except Exception as e:
            logger.error(f"Error calculating component scores: {e}")
            # Return default scores
            scores = {key: 0.0 for key in ['stars', 'forks', 'contributors', 'commit_frequency', 
                                         'trend_growth', 'issue_resolution', 'code_health']}
        
        return scores
    
    def _calculate_ai_relevance_score(self, repo_data: Dict[str, Any]) -> float:
        """Calculate AI relevance score based on repository content"""
        try:
            score = 0.0
            
            # AI keywords in name and description
            ai_keywords = {
                'high': ['artificial intelligence', 'machine learning', 'deep learning', 'neural network'],
                'medium': ['ai', 'ml', 'nlp', 'computer vision', 'reinforcement learning', 'tensorflow', 'pytorch'],
                'low': ['automation', 'chatbot', 'gpt', 'llm', 'transformer', 'bert', 'generative']
            }
            
            repo_text = f"{repo_data.get('name', '')} {repo_data.get('description', '')}".lower()
            topics = [topic.lower() for topic in repo_data.get('topics', [])]
            
            # Check keywords
            for level, keywords in ai_keywords.items():
                for keyword in keywords:
                    if keyword in repo_text or keyword in topics:
                        if level == 'high':
                            score += 0.3
                        elif level == 'medium':
                            score += 0.2
                        else:
                            score += 0.1
            
            # Language relevance
            language = repo_data.get('language', '').lower()
            ai_languages = ['python', 'jupyter notebook', 'r', 'julia', 'swift', 'c++']
            if language in ai_languages:
                score += 0.2
            
            # README content analysis (if available)
            readme_content = repo_data.get('readme_content', '')
            if readme_content:
                readme_text = readme_content.lower()
                ai_concepts = ['model', 'training', 'dataset', 'algorithm', 'prediction', 'classification', 
                             'regression', 'clustering', 'neural', 'embedding', 'vector', 'matrix']
                
                concept_count = sum(1 for concept in ai_concepts if concept in readme_text)
                score += min(concept_count * 0.05, 0.3)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating AI relevance score: {e}")
            return 0.0
    
    def _calculate_quality_score(self, 
                               repo_data: Dict[str, Any], 
                               metrics: Dict[str, Any] = None) -> float:
        """Calculate code quality score"""
        try:
            score = 0.0
            
            # Has README
            if repo_data.get('readme_content'):
                score += 0.2
            
            # Has license
            if repo_data.get('license'):
                score += 0.15
            
            # Not a fork
            if not repo_data.get('fork', False):
                score += 0.15
            
            # Has issues enabled (indicates active maintenance)
            if repo_data.get('has_issues', True):
                score += 0.1
            
            # Has wiki
            if repo_data.get('has_wiki', False):
                score += 0.1
            
            # Has pages
            if repo_data.get('has_pages', False):
                score += 0.1
            
            # Branch protection (indicates good practices)
            if repo_data.get('allow_forking', False):
                score += 0.1
            
            # Default branch protection (can't determine from API, assume based on activity)
            if metrics and metrics.get('commit_frequency', 0) > 0.5:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _calculate_popularity_score(self, repo_data: Dict[str, Any]) -> float:
        """Calculate popularity score"""
        try:
            score = 0.0
            
            # Stars (logarithmic)
            stars = repo_data.get('stargazers_count', 0)
            score += min(np.log10(max(stars, 1)) / 5.0, 0.4)
            
            # Forks
            forks = repo_data.get('forks_count', 0)
            score += min(np.log10(max(forks, 1)) / 4.0, 0.3)
            
            # Watchers
            watchers = repo_data.get('watchers_count', 0)
            score += min(np.log10(max(watchers, 1)) / 4.0, 0.2)
            
            # Subscribers
            subscribers = repo_data.get('subscribers_count', 0)
            score += min(subscribers / 100.0, 0.1)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating popularity score: {e}")
            return 0.0
    
    def _calculate_activity_score(self, 
                                repo_data: Dict[str, Any], 
                                metrics: Dict[str, Any] = None) -> float:
        """Calculate activity score"""
        try:
            score = 0.0
            
            if not metrics:
                return 0.0
            
            # Recent commits
            commit_frequency = metrics.get('commit_frequency', 0)
            score += min(commit_frequency / 5.0, 0.4)  # 5 commits/day = 1.0
            
            # Contributor activity
            contributor_activity = metrics.get('contributor_activity', 0)
            score += contributor_activity * 0.3
            
            # Recent updates
            updated_at = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
            days_since_update = (datetime.utcnow() - updated_at.replace(tzinfo=None)).days
            
            if days_since_update <= 7:
                score += 0.2
            elif days_since_update <= 30:
                score += 0.15
            elif days_since_update <= 90:
                score += 0.1
            else:
                score += 0.05
            
            # Issue activity
            open_issues = repo_data.get('open_issues_count', 0)
            if open_issues > 0:
                score += min(open_issues / 50.0, 0.1)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating activity score: {e}")
            return 0.0
    
    def _calculate_trend_score(self, 
                             repo_data: Dict[str, Any], 
                             metrics: Dict[str, Any] = None) -> float:
        """Calculate trend score"""
        try:
            score = 0.0
            
            if not metrics:
                return 0.0
            
            # Stars growth rate
            stars_growth = metrics.get('stars_growth_rate', 0)
            if stars_growth > 0:
                score += min(stars_growth * 2, 0.4)  # 20% growth = 0.4
            
            # Forks growth rate
            forks_growth = metrics.get('forks_growth_rate', 0)
            if forks_growth > 0:
                score += min(forks_growth * 2, 0.3)
            
            # New contributors
            new_contributors = metrics.get('new_contributors', 0)
            score += min(new_contributors / 10.0, 0.2)
            
            # Velocity (commits per contributor)
            contributors = metrics.get('contributors_count', 1)
            commits_30_days = metrics.get('commits_30_days', 0)
            if contributors > 0:
                velocity = commits_30_days / contributors
                score += min(velocity / 20.0, 0.1)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.0
    
    def _calculate_code_health_score(self, 
                                   repo_data: Dict[str, Any], 
                                   metrics: Dict[str, Any] = None) -> float:
        """Calculate code health score"""
        try:
            score = 0.0
            
            # Repository size (not too large, not too small)
            size = repo_data.get('size', 0)
            if 100 <= size <= 50000:  # Reasonable size
                score += 0.2
            elif size < 100:
                score += 0.1  # Very small, might be incomplete
            
            # Issue ratio (not too many open issues)
            open_issues = repo_data.get('open_issues_count', 0)
            stars = repo_data.get('stargazers_count', 1)
            issue_ratio = open_issues / stars
            
            if issue_ratio < 0.1:
                score += 0.3
            elif issue_ratio < 0.2:
                score += 0.2
            else:
                score += 0.1
            
            # Fork vs star ratio (indicates genuine interest)
            forks = repo_data.get('forks_count', 0)
            fork_ratio = forks / stars if stars > 0 else 0
            
            if 0.1 <= fork_ratio <= 0.5:
                score += 0.2
            else:
                score += 0.1
            
            # Community engagement
            if metrics:
                contributor_activity = metrics.get('contributor_activity', 0)
                score += contributor_activity * 0.3
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating code health score: {e}")
            return 0.0
    
    def _calculate_overall_score(self, evaluation: Dict[str, Any]) -> float:
        """Calculate overall weighted score"""
        try:
            component_scores = evaluation.get('component_scores', {})
            
            overall_score = 0.0
            for component, weight in self.scoring_weights.items():
                score = component_scores.get(component, 0.0)
                overall_score += score * weight
            
            # Bonus for high AI relevance
            ai_bonus = evaluation.get('ai_relevance_score', 0.0) * 0.1
            overall_score += ai_bonus
            
            return min(overall_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    def _generate_recommendations(self, 
                                evaluation: Dict[str, Any], 
                                repo_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on evaluation"""
        recommendations = []
        
        try:
            component_scores = evaluation.get('component_scores', {})
            
            # Low activity recommendations
            if evaluation.get('activity_score', 0) < 0.3:
                recommendations.append("Low recent activity - project may be stagnant")
            
            # Low quality recommendations
            if evaluation.get('quality_score', 0) < 0.4:
                if not repo_data.get('readme_content'):
                    recommendations.append("Missing README - add documentation to improve quality")
                if not repo_data.get('license'):
                    recommendations.append("No license - add a license for better adoption")
            
            # Low popularity recommendations
            if evaluation.get('popularity_score', 0) < 0.2:
                recommendations.append("Low popularity - consider more established alternatives")
            
            # High trend recommendations
            if evaluation.get('trend_score', 0) > 0.7:
                recommendations.append("High trending growth - promising emerging project")
            
            # High AI relevance recommendations
            if evaluation.get('ai_relevance_score', 0) > 0.8:
                recommendations.append("Highly relevant to AI/ML - excellent domain fit")
            
            # Code health recommendations
            if component_scores.get('code_health', 0) < 0.3:
                recommendations.append("Code health concerns - review issue backlog and maintenance")
            
            # Contributor recommendations
            contributors = repo_data.get('contributors_count', 0)
            if contributors < 3:
                recommendations.append("Few contributors - potential bus factor risk")
            elif contributors > 50:
                recommendations.append("Large contributor base - active community project")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def batch_evaluate_repositories(self, 
                                  repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluate multiple repositories"""
        evaluations = []
        
        for repo_data in repositories:
            try:
                evaluation = self.evaluate_repository(repo_data)
                if evaluation:
                    evaluations.append(evaluation)
            except Exception as e:
                logger.error(f"Failed to evaluate repository {repo_data.get('full_name', 'unknown')}: {e}")
                continue
        
        return evaluations
    
    def get_top_repositories(self, 
                           evaluations: List[Dict[str, Any]], 
                           top_n: int = 10,
                           sort_by: str = 'overall_score') -> List[Dict[str, Any]]:
        """Get top repositories by score"""
        try:
            sorted_evaluations = sorted(
                evaluations, 
                key=lambda x: x.get(sort_by, 0), 
                reverse=True
            )
            return sorted_evaluations[:top_n]
        except Exception as e:
            logger.error(f"Error getting top repositories: {e}")
            return []
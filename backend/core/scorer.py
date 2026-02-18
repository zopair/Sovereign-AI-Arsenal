import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from ..database.models import Repository, Trend, RepositoryMetrics
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class RepositoryScorer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scoring_weights = config.get('scoring', {}).get('weights', {
            'stars': 0.25,
            'forks': 0.15,
            'contributors': 0.20,
            'commit_frequency': 0.15,
            'trend_growth': 0.15,
            'community_health': 0.10
        })
        self.thresholds = config.get('scoring', {}).get('thresholds', {
            'minimum_stars': 30,
            'trending_growth_rate': 0.1,
            'active_contributors': 3
        })
    
    def calculate_composite_score(self, 
                                repo_data: Dict[str, Any], 
                                metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate comprehensive repository score"""
        try:
            # Initialize score components
            scores = {
                'popularity_score': 0.0,
                'activity_score': 0.0,
                'community_score': 0.0,
                'trend_score': 0.0,
                'quality_score': 0.0,
                'potential_score': 0.0,
                'overall_score': 0.0
            }
            
            # Calculate individual scores
            scores['popularity_score'] = self._calculate_popularity_score(repo_data)
            scores['activity_score'] = self._calculate_activity_score(repo_data, metrics)
            scores['community_score'] = self._calculate_community_score(repo_data, metrics)
            scores['trend_score'] = self._calculate_trend_score(repo_data, metrics)
            scores['quality_score'] = self._calculate_quality_score(repo_data, metrics)
            scores['potential_score'] = self._calculate_potential_score(repo_data, metrics)
            
            # Calculate weighted overall score
            scores['overall_score'] = self._calculate_weighted_score(scores)
            
            # Add metadata
            scores.update({
                'repo_id': repo_data.get('id'),
                'repo_name': repo_data.get('full_name'),
                'calculated_at': datetime.utcnow().isoformat(),
                'score_breakdown': {
                    'weights': self.scoring_weights,
                    'components': self._get_score_components(scores)
                }
            })
            
            return scores
            
        except Exception as e:
            logger.error(f"Failed to calculate composite score: {e}")
            return {}
    
    def _calculate_popularity_score(self, repo_data: Dict[str, Any]) -> float:
        """Calculate popularity score based on stars, forks, and watchers"""
        try:
            stars = repo_data.get('stargazers_count', 0)
            forks = repo_data.get('forks_count', 0)
            watchers = repo_data.get('watchers_count', 0)
            subscribers = repo_data.get('subscribers_count', 0)
            
            # Logarithmic scaling for stars (to handle wide range)
            star_score = np.log10(max(stars, 1)) / 6.0  # Normalize to 0-1
            star_score = min(star_score, 1.0)
            
            # Fork score
            fork_score = np.log10(max(forks, 1)) / 5.0
            fork_score = min(fork_score, 1.0)
            
            # Watcher score
            watcher_score = np.log10(max(watchers, 1)) / 4.0
            watcher_score = min(watcher_score, 1.0)
            
            # Subscriber score
            subscriber_score = min(subscribers / 100.0, 1.0)
            
            # Weighted combination
            popularity_score = (
                star_score * 0.5 +
                fork_score * 0.25 +
                watcher_score * 0.15 +
                subscriber_score * 0.1
            )
            
            return min(popularity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating popularity score: {e}")
            return 0.0
    
    def _calculate_activity_score(self, 
                                repo_data: Dict[str, Any], 
                                metrics: Dict[str, Any] = None) -> float:
        """Calculate activity score based on recent commits and updates"""
        try:
            if not metrics:
                return 0.0
            
            # Commit frequency (commits per day)
            commit_frequency = metrics.get('commit_frequency', 0)
            commit_score = min(commit_frequency / 5.0, 1.0)  # 5 commits/day = 1.0
            
            # Recent updates
            updated_at = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
            days_since_update = (datetime.utcnow() - updated_at.replace(tzinfo=None)).days
            
            if days_since_update <= 1:
                recency_score = 1.0
            elif days_since_update <= 7:
                recency_score = 0.8
            elif days_since_update <= 30:
                recency_score = 0.6
            elif days_since_update <= 90:
                recency_score = 0.4
            elif days_since_update <= 180:
                recency_score = 0.2
            else:
                recency_score = 0.1
            
            # Issue activity
            open_issues = repo_data.get('open_issues_count', 0)
            issue_score = min(open_issues / 50.0, 1.0) * 0.3  # Cap impact
            
            # Pull request activity (if available)
            pr_score = 0.0
            if metrics.get('pull_requests_merged', 0):
                pr_score = min(metrics['pull_requests_merged'] / 20.0, 1.0) * 0.2
            
            activity_score = (
                commit_score * 0.4 +
                recency_score * 0.3 +
                issue_score * 0.2 +
                pr_score * 0.1
            )
            
            return min(activity_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating activity score: {e}")
            return 0.0
    
    def _calculate_community_score(self, 
                                 repo_data: Dict[str, Any], 
                                 metrics: Dict[str, Any] = None) -> float:
        """Calculate community health score"""
        try:
            if not metrics:
                return 0.0
            
            # Contributor count and diversity
            contributors = metrics.get('contributors_count', 0)
            contributor_score = min(contributors / 20.0, 1.0)
            
            # Contributor activity ratio
            total_contributions = metrics.get('total_contributions', 0)
            active_contributors = metrics.get('active_contributors', contributors)
            
            if contributors > 0:
                activity_ratio = active_contributors / contributors
                diversity_score = activity_ratio
            else:
                diversity_score = 0.0
            
            # Bus factor (how many contributors make up 50% of contributions)
            bus_factor = metrics.get('bus_factor', 1)
            bus_score = min(bus_factor / 10.0, 1.0)
            
            # Issue resolution rate
            issues_opened = metrics.get('issues_opened', 0)
            issues_closed = metrics.get('issues_closed', 0)
            total_issues = issues_opened + issues_closed
            
            if total_issues > 0:
                resolution_rate = issues_closed / total_issues
                resolution_score = resolution_rate
            else:
                resolution_score = 0.5  # Neutral score
            
            community_score = (
                contributor_score * 0.3 +
                diversity_score * 0.25 +
                bus_score * 0.25 +
                resolution_score * 0.2
            )
            
            return min(community_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating community score: {e}")
            return 0.0
    
    def _calculate_trend_score(self, 
                             repo_data: Dict[str, Any], 
                             metrics: Dict[str, Any] = None) -> float:
        """Calculate trend score based on growth metrics"""
        try:
            if not metrics:
                return 0.0
            
            # Stars growth rate
            stars_growth = metrics.get('stars_growth_rate', 0)
            if stars_growth > 0:
                stars_trend = min(stars_growth * 2, 1.0)  # 50% growth = 1.0
            else:
                stars_trend = 0.0
            
            # Forks growth rate
            forks_growth = metrics.get('forks_growth_rate', 0)
            if forks_growth > 0:
                forks_trend = min(forks_growth * 2, 1.0)
            else:
                forks_trend = 0.0
            
            # New contributors trend
            new_contributors = metrics.get('new_contributors', 0)
            contributors_trend = min(new_contributors / 10.0, 1.0)
            
            # Commit velocity trend
            current_velocity = metrics.get('commit_frequency', 0)
            previous_velocity = metrics.get('previous_commit_frequency', current_velocity)
            
            if previous_velocity > 0:
                velocity_trend = min((current_velocity - previous_velocity) / previous_velocity, 1.0)
                velocity_trend = max(velocity_trend, -1.0)  # Cap negative
                velocity_trend = (velocity_trend + 1) / 2  # Convert to 0-1
            else:
                velocity_trend = 0.5
            
            # Weekly growth rate
            weekly_growth = metrics.get('weekly_growth_rate', 0)
            weekly_trend = max(min(weekly_growth * 5, 1.0), 0.0)
            
            trend_score = (
                stars_trend * 0.3 +
                forks_trend * 0.2 +
                contributors_trend * 0.2 +
                velocity_trend * 0.15 +
                weekly_trend * 0.15
            )
            
            return min(trend_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.0
    
    def _calculate_quality_score(self, 
                               repo_data: Dict[str, Any], 
                               metrics: Dict[str, Any] = None) -> float:
        """Calculate code quality and maintenance score"""
        try:
            quality_score = 0.0
            
            # Documentation quality
            if repo_data.get('readme_content'):
                quality_score += 0.2
            
            # License
            if repo_data.get('license'):
                quality_score += 0.15
            
            # Not a fork (original work)
            if not repo_data.get('fork', False):
                quality_score += 0.15
            
            # Repository size (reasonable size indicates mature project)
            size = repo_data.get('size', 0)
            if 100 <= size <= 50000:
                quality_score += 0.1
            elif size > 50000:
                quality_score += 0.05  # Large but established
            
            # Issue management
            if repo_data.get('has_issues', True):
                quality_score += 0.1
            
            # Wiki and documentation
            if repo_data.get('has_wiki', False):
                quality_score += 0.1
            
            # CI/CD indicators
            if repo_data.get('has_pages', False):
                quality_score += 0.05
            
            # Branch protection (good practices)
            if repo_data.get('allow_forking', False):
                quality_score += 0.05
            
            # Code health metrics
            if metrics:
                # Low issue ratio
                open_issues = repo_data.get('open_issues_count', 0)
                stars = repo_data.get('stargazers_count', 1)
                issue_ratio = open_issues / stars if stars > 0 else 1
                
                if issue_ratio < 0.05:
                    quality_score += 0.1
                elif issue_ratio < 0.1:
                    quality_score += 0.05
                
                # Technical debt (inverse)
                tech_debt = metrics.get('technical_debt', 0)
                quality_score += max(0, 0.1 - tech_debt)
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _calculate_potential_score(self, 
                                 repo_data: Dict[str, Any], 
                                 metrics: Dict[str, Any] = None) -> float:
        """Calculate future potential score"""
        try:
            potential_score = 0.0
            
            # Age of repository (not too new, not too old)
            created_at = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
            age_days = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
            
            if 30 <= age_days <= 365:  # Sweet spot
                potential_score += 0.2
            elif age_days < 30:
                potential_score += 0.1  # Too new to judge
            elif age_days <= 1095:  # Up to 3 years
                potential_score += 0.15
            
            # Growth acceleration
            if metrics:
                stars_growth = metrics.get('stars_growth_rate', 0)
                if stars_growth > 0.2:  # 20%+ growth
                    potential_score += 0.2
                elif stars_growth > 0.1:
                    potential_score += 0.1
                
                # Contributor growth
                contributor_growth = metrics.get('contributor_growth_rate', 0)
                if contributor_growth > 0.1:
                    potential_score += 0.15
                
                # Innovation indicators
                commit_frequency = metrics.get('commit_frequency', 0)
                if commit_frequency > 2.0:  # High activity
                    potential_score += 0.15
            
            # Technology relevance
            language = repo_data.get('language', '').lower()
            hot_languages = ['python', 'jupyter notebook', 'rust', 'go', 'typescript', 'swift']
            if language in hot_languages:
                potential_score += 0.1
            
            # Topic relevance
            topics = [topic.lower() for topic in repo_data.get('topics', [])]
            hot_topics = ['machine learning', 'artificial intelligence', 'deep learning', 
                         'blockchain', 'web3', 'kubernetes', 'microservices']
            
            topic_matches = sum(1 for topic in hot_topics if topic in topics)
            potential_score += min(topic_matches * 0.05, 0.2)
            
            return min(potential_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating potential score: {e}")
            return 0.0
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate final weighted score"""
        try:
            # Map scoring weights to score components
            weight_mapping = {
                'popularity_score': self.scoring_weights.get('stars', 0.25),
                'activity_score': self.scoring_weights.get('commit_frequency', 0.15),
                'community_score': self.scoring_weights.get('contributors', 0.20),
                'trend_score': self.scoring_weights.get('trend_growth', 0.15),
                'quality_score': 0.10,  # Fixed weight for quality
                'potential_score': 0.15  # Fixed weight for potential
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for score_name, weight in weight_mapping.items():
                score_value = scores.get(score_name, 0.0)
                weighted_score += score_value * weight
                total_weight += weight
            
            # Normalize by total weight
            if total_weight > 0:
                weighted_score /= total_weight
            
            return min(weighted_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}")
            return 0.0
    
    def _get_score_components(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Get score components for breakdown"""
        return {
            'popularity': scores.get('popularity_score', 0.0),
            'activity': scores.get('activity_score', 0.0),
            'community': scores.get('community_score', 0.0),
            'trend': scores.get('trend_score', 0.0),
            'quality': scores.get('quality_score', 0.0),
            'potential': scores.get('potential_score', 0.0)
        }
    
    def batch_score_repositories(self, 
                                repositories_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple repositories"""
        scores_list = []
        
        for repo_data in repositories_data:
            try:
                metrics = repo_data.get('metrics', {})
                scores = self.calculate_composite_score(repo_data, metrics)
                if scores:
                    scores_list.append(scores)
            except Exception as e:
                logger.error(f"Failed to score repository {repo_data.get('full_name', 'unknown')}: {e}")
                continue
        
        return scores_list
    
    def get_top_repositories(self, 
                           scores_list: List[Dict[str, Any]], 
                           top_n: int = 10,
                           sort_by: str = 'overall_score') -> List[Dict[str, Any]]:
        """Get top repositories by score"""
        try:
            sorted_scores = sorted(
                scores_list,
                key=lambda x: x.get(sort_by, 0),
                reverse=True
            )
            return sorted_scores[:top_n]
        except Exception as e:
            logger.error(f"Error getting top repositories: {e}")
            return []
    
    def get_score_statistics(self, scores_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about scores"""
        try:
            if not scores_list:
                return {}
            
            score_types = ['overall_score', 'popularity_score', 'activity_score', 
                          'community_score', 'trend_score', 'quality_score', 'potential_score']
            
            stats = {}
            for score_type in score_types:
                values = [s.get(score_type, 0) for s in scores_list if score_type in s]
                if values:
                    stats[score_type] = {
                        'mean': np.mean(values),
                        'median': np.median(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values)
                    }
            
            stats['total_repositories'] = len(scores_list)
            stats['score_distribution'] = {
                'high_performers': len([s for s in scores_list if s.get('overall_score', 0) > 0.8]),
                'average_performers': len([s for s in scores_list if 0.5 <= s.get('overall_score', 0) <= 0.8]),
                'low_performers': len([s for s in scores_list if s.get('overall_score', 0) < 0.5])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating score statistics: {e}")
            return {}
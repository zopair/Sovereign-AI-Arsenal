import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from ..database.models import Repository, Trend, RepositoryMetrics
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class TrendAnalysisEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trend_thresholds = config.get('trend_thresholds', {
            'explosive_growth': 0.5,      # 50%+ weekly growth
            'high_growth': 0.2,           # 20%+ weekly growth
            'moderate_growth': 0.1,       # 10%+ weekly growth
            'low_growth': 0.05,           # 5%+ weekly growth
            'stagnant': 0.0,              # 0% growth
            'declining': -0.05            # -5%+ growth
        })
    
    def analyze_repository_trends(self, 
                                repo_data: Dict[str, Any], 
                                historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze trends for a repository"""
        try:
            trend_analysis = {
                'repo_id': repo_data.get('id'),
                'repo_name': repo_data.get('full_name'),
                'analysis_date': datetime.utcnow().isoformat(),
                'trend_metrics': {},
                'growth_patterns': {},
                'trend_classification': {},
                'predictions': {},
                'insights': []
            }
            
            # Calculate trend metrics
            trend_analysis['trend_metrics'] = self._calculate_trend_metrics(repo_data, historical_data)
            
            # Analyze growth patterns
            trend_analysis['growth_patterns'] = self._analyze_growth_patterns(trend_analysis['trend_metrics'])
            
            # Classify trends
            trend_analysis['trend_classification'] = self._classify_trends(trend_analysis['growth_patterns'])
            
            # Generate predictions
            trend_analysis['predictions'] = self._generate_predictions(trend_analysis['trend_metrics'])
            
            # Generate insights
            trend_analysis['insights'] = self._generate_insights(trend_analysis)
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze repository trends: {e}")
            return {}
    
    def _calculate_trend_metrics(self, 
                               repo_data: Dict[str, Any], 
                               historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate various trend metrics"""
        try:
            metrics = {}
            
            # Current metrics
            current_stars = repo_data.get('stargazers_count', 0)
            current_forks = repo_data.get('forks_count', 0)
            current_contributors = repo_data.get('contributors_count', 0)
            
            # Calculate growth rates (if historical data available)
            if historical_data and len(historical_data) >= 2:
                # Sort by date
                sorted_data = sorted(historical_data, key=lambda x: x.get('date', ''))
                
                # Get recent data points
                recent = sorted_data[-1]
                previous = sorted_data[-2]
                
                # Time difference in days
                time_diff = self._calculate_time_difference(previous.get('date'), recent.get('date'))
                
                if time_diff > 0:
                    # Calculate growth rates
                    metrics['stars_growth_rate'] = self._calculate_growth_rate(
                        previous.get('stars', 0), recent.get('stars', 0), time_diff
                    )
                    metrics['forks_growth_rate'] = self._calculate_growth_rate(
                        previous.get('forks', 0), recent.get('forks', 0), time_diff
                    )
                    metrics['contributors_growth_rate'] = self._calculate_growth_rate(
                        previous.get('contributors', 0), recent.get('contributors', 0), time_diff
                    )
                    
                    # Calculate weekly growth rates
                    metrics['weekly_stars_growth'] = metrics['stars_growth_rate'] * 7
                    metrics['weekly_forks_growth'] = metrics['forks_growth_rate'] * 7
                    metrics['weekly_contributors_growth'] = metrics['contributors_growth_rate'] * 7
                else:
                    metrics.update(self._default_growth_rates())
            else:
                metrics.update(self._default_growth_rates())
            
            # Calculate momentum metrics
            metrics['momentum'] = self._calculate_momentum(repo_data, historical_data)
            
            # Calculate velocity metrics
            metrics['velocity'] = self._calculate_velocity(repo_data, historical_data)
            
            # Calculate acceleration
            metrics['acceleration'] = self._calculate_acceleration(historical_data)
            
            # Calculate trend strength
            metrics['trend_strength'] = self._calculate_trend_strength(historical_data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating trend metrics: {e}")
            return self._default_trend_metrics()
    
    def _calculate_growth_rate(self, previous_value: float, current_value: float, time_diff: float) -> float:
        """Calculate growth rate per day"""
        if previous_value == 0:
            return 0.0
        
        growth_rate = (current_value - previous_value) / previous_value
        daily_rate = growth_rate / time_diff if time_diff > 0 else 0.0
        return daily_rate
    
    def _calculate_time_difference(self, date1: str, date2: str) -> float:
        """Calculate time difference in days between two dates"""
        try:
            if not date1 or not date2:
                return 1.0
            
            dt1 = datetime.fromisoformat(date1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(date2.replace('Z', '+00:00'))
            
            diff = abs((dt2 - dt1).total_seconds()) / 86400  # Convert to days
            return max(diff, 1.0)  # Minimum 1 day
            
        except Exception as e:
            logger.error(f"Error calculating time difference: {e}")
            return 1.0
    
    def _calculate_momentum(self, repo_data: Dict[str, Any], historical_data: List[Dict[str, Any]] = None) -> Dict[str, float]:
        """Calculate momentum indicators"""
        try:
            momentum = {}
            
            # Star momentum (stars per day since creation)
            created_at = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
            age_days = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
            current_stars = repo_data.get('stargazers_count', 0)
            
            momentum['stars_per_day'] = current_stars / max(age_days, 1)
            momentum['stars_per_week'] = momentum['stars_per_day'] * 7
            momentum['stars_per_month'] = momentum['stars_per_day'] * 30
            
            # Fork momentum
            current_forks = repo_data.get('forks_count', 0)
            momentum['forks_per_day'] = current_forks / max(age_days, 1)
            momentum['forks_per_week'] = momentum['forks_per_day'] * 7
            
            # Recent momentum (last 30 days)
            if historical_data:
                recent_data = [d for d in historical_data if self._is_recent_data(d.get('date'), 30)]
                if len(recent_data) >= 2:
                    recent = recent_data[-1]
                    previous = recent_data[0]
                    
                    time_diff = self._calculate_time_difference(previous.get('date'), recent.get('date'))
                    
                    if time_diff > 0:
                        momentum['recent_stars_per_day'] = (recent.get('stars', 0) - previous.get('stars', 0)) / time_diff
                        momentum['recent_forks_per_day'] = (recent.get('forks', 0) - previous.get('forks', 0)) / time_diff
                    else:
                        momentum['recent_stars_per_day'] = 0.0
                        momentum['recent_forks_per_day'] = 0.0
                else:
                    momentum['recent_stars_per_day'] = momentum['stars_per_day']
                    momentum['recent_forks_per_day'] = momentum['forks_per_day']
            else:
                momentum['recent_stars_per_day'] = momentum['stars_per_day']
                momentum['recent_forks_per_day'] = momentum['forks_per_day']
            
            return momentum
            
        except Exception as e:
            logger.error(f"Error calculating momentum: {e}")
            return {}
    
    def _calculate_velocity(self, repo_data: Dict[str, Any], historical_data: List[Dict[str, Any]] = None) -> Dict[str, float]:
        """Calculate velocity metrics"""
        try:
            velocity = {}
            
            # Commit velocity
            commits_30_days = repo_data.get('commits_30_days', 0)
            velocity['commits_per_day'] = commits_30_days / 30.0
            velocity['commits_per_week'] = commits_30_days / 4.33  # Average weeks in month
            
            # Contributor velocity
            contributors = repo_data.get('contributors_count', 1)
            velocity['commits_per_contributor'] = commits_30_days / max(contributors, 1)
            
            # Issue resolution velocity
            issues_opened = repo_data.get('issues_opened', 0)
            issues_closed = repo_data.get('issues_closed', 0)
            total_issues = issues_opened + issues_closed
            
            if total_issues > 0:
                velocity['issue_resolution_rate'] = issues_closed / total_issues
            else:
                velocity['issue_resolution_rate'] = 0.5  # Neutral
            
            # PR velocity
            prs_opened = repo_data.get('pull_requests_opened', 0)
            prs_merged = repo_data.get('pull_requests_merged', 0)
            
            if prs_opened > 0:
                velocity['pr_merge_rate'] = prs_merged / prs_opened
            else:
                velocity['pr_merge_rate'] = 0.5  # Neutral
            
            return velocity
            
        except Exception as e:
            logger.error(f"Error calculating velocity: {e}")
            return {}
    
    def _calculate_acceleration(self, historical_data: List[Dict[str, Any]] = None) -> Dict[str, float]:
        """Calculate acceleration (change in growth rate)"""
        try:
            acceleration = {}
            
            if not historical_data or len(historical_data) < 3:
                return {'stars_acceleration': 0.0, 'forks_acceleration': 0.0, 'contributors_acceleration': 0.0}
            
            # Sort by date
            sorted_data = sorted(historical_data, key=lambda x: x.get('date', ''))
            
            # Calculate acceleration for each metric
            for metric in ['stars', 'forks', 'contributors']:
                values = [d.get(metric, 0) for d in sorted_data]
                dates = [d.get('date') for d in sorted_data]
                
                if len(values) >= 3:
                    # Calculate growth rates for consecutive periods
                    growth_rates = []
                    for i in range(1, len(values)):
                        time_diff = self._calculate_time_difference(dates[i-1], dates[i])
                        if time_diff > 0:
                            growth_rate = self._calculate_growth_rate(values[i-1], values[i], time_diff)
                            growth_rates.append(growth_rate)
                    
                    # Calculate acceleration (change in growth rates)
                    if len(growth_rates) >= 2:
                        accel = growth_rates[-1] - growth_rates[0]
                        acceleration[f'{metric}_acceleration'] = accel
                    else:
                        acceleration[f'{metric}_acceleration'] = 0.0
                else:
                    acceleration[f'{metric}_acceleration'] = 0.0
            
            return acceleration
            
        except Exception as e:
            logger.error(f"Error calculating acceleration: {e}")
            return {'stars_acceleration': 0.0, 'forks_acceleration': 0.0, 'contributors_acceleration': 0.0}
    
    def _calculate_trend_strength(self, historical_data: List[Dict[str, Any]] = None) -> float:
        """Calculate overall trend strength (0-1)"""
        try:
            if not historical_data or len(historical_data) < 2:
                return 0.5  # Neutral
            
            # Calculate correlation coefficient for trend
            sorted_data = sorted(historical_data, key=lambda x: x.get('date', ''))
            
            # Use stars as primary indicator
            stars_values = [d.get('stars', 0) for d in sorted_data]
            
            if len(stars_values) < 2:
                return 0.5
            
            # Calculate trend line
            x = np.arange(len(stars_values))
            y = np.array(stars_values)
            
            # Calculate correlation coefficient
            if len(x) > 1 and np.std(y) > 0:
                correlation = np.corrcoef(x, y)[0, 1]
                # Convert to 0-1 scale
                trend_strength = (correlation + 1) / 2
                return max(0, min(1, trend_strength))
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return 0.5
    
    def _analyze_growth_patterns(self, trend_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze growth patterns"""
        try:
            patterns = {}
            
            # Growth pattern classification
            weekly_growth = trend_metrics.get('weekly_stars_growth', 0)
            
            if weekly_growth >= self.trend_thresholds['explosive_growth']:
                patterns['growth_pattern'] = 'explosive'
            elif weekly_growth >= self.trend_thresholds['high_growth']:
                patterns['growth_pattern'] = 'high'
            elif weekly_growth >= self.trend_thresholds['moderate_growth']:
                patterns['growth_pattern'] = 'moderate'
            elif weekly_growth >= self.trend_thresholds['low_growth']:
                patterns['growth_pattern'] = 'low'
            elif weekly_growth >= self.trend_thresholds['stagnant']:
                patterns['growth_pattern'] = 'stagnant'
            else:
                patterns['growth_pattern'] = 'declining'
            
            # Momentum pattern
            momentum = trend_metrics.get('momentum', {})
            recent_stars_per_day = momentum.get('recent_stars_per_day', 0)
            overall_stars_per_day = momentum.get('stars_per_day', 0)
            
            if recent_stars_per_day > overall_stars_per_day * 1.5:
                patterns['momentum_pattern'] = 'accelerating'
            elif recent_stars_per_day < overall_stars_per_day * 0.5:
                patterns['momentum_pattern'] = 'decelerating'
            else:
                patterns['momentum_pattern'] = 'stable'
            
            # Velocity pattern
            velocity = trend_metrics.get('velocity', {})
            commits_per_day = velocity.get('commits_per_day', 0)
            commits_per_contributor = velocity.get('commits_per_contributor', 0)
            
            if commits_per_day > 2 and commits_per_contributor > 5:
                patterns['velocity_pattern'] = 'high'
            elif commits_per_day > 0.5 and commits_per_contributor > 1:
                patterns['velocity_pattern'] = 'moderate'
            else:
                patterns['velocity_pattern'] = 'low'
            
            # Acceleration pattern
            acceleration = trend_metrics.get('acceleration', {})
            stars_acceleration = acceleration.get('stars_acceleration', 0)
            
            if stars_acceleration > 0.01:
                patterns['acceleration_pattern'] = 'positive'
            elif stars_acceleration < -0.01:
                patterns['acceleration_pattern'] = 'negative'
            else:
                patterns['acceleration_pattern'] = 'neutral'
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing growth patterns: {e}")
            return {}
    
    def _classify_trends(self, growth_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Classify trends into categories"""
        try:
            classification = {}
            
            # Overall trend classification
            growth_pattern = growth_patterns.get('growth_pattern', 'stagnant')
            momentum_pattern = growth_patterns.get('momentum_pattern', 'stable')
            velocity_pattern = growth_patterns.get('velocity_pattern', 'low')
            
            # Determine overall trend
            if growth_pattern in ['explosive', 'high'] and momentum_pattern == 'accelerating':
                classification['overall_trend'] = 'hot'
                classification['trend_level'] = 9
            elif growth_pattern in ['moderate', 'high'] and momentum_pattern in ['accelerating', 'stable']:
                classification['overall_trend'] = 'warm'
                classification['trend_level'] = 7
            elif growth_pattern == 'moderate' and momentum_pattern == 'stable':
                classification['overall_trend'] = 'steady'
                classification['trend_level'] = 5
            elif growth_pattern == 'low' or momentum_pattern == 'decelerating':
                classification['overall_trend'] = 'cool'
                classification['trend_level'] = 3
            else:
                classification['overall_trend'] = 'cold'
                classification['trend_level'] = 1
            
            # Risk assessment
            if growth_pattern == 'declining' and velocity_pattern == 'low':
                classification['risk_level'] = 'high'
            elif growth_pattern in ['stagnant', 'declining']:
                classification['risk_level'] = 'medium'
            else:
                classification['risk_level'] = 'low'
            
            # Investment recommendation
            trend_level = classification.get('trend_level', 1)
            if trend_level >= 8:
                classification['investment_recommendation'] = 'strong_buy'
            elif trend_level >= 6:
                classification['investment_recommendation'] = 'buy'
            elif trend_level >= 4:
                classification['investment_recommendation'] = 'hold'
            else:
                classification['investment_recommendation'] = 'avoid'
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying trends: {e}")
            return {}
    
    def _generate_predictions(self, trend_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate future predictions based on trends"""
        try:
            predictions = {}
            
            # Current metrics
            current_stars = trend_metrics.get('current_stars', 0)
            current_forks = trend_metrics.get('current_forks', 0)
            
            # Growth rates
            weekly_stars_growth = trend_metrics.get('weekly_stars_growth', 0)
            weekly_forks_growth = trend_metrics.get('weekly_forks_growth', 0)
            
            # Predictions for different time horizons
            time_horizons = [7, 30, 90, 365]  # days
            
            for days in time_horizons:
                weeks = days / 7
                
                # Stars prediction
                predicted_stars = current_stars * (1 + weekly_stars_growth) ** weeks
                predictions[f'stars_{days}d'] = int(predicted_stars)
                
                # Forks prediction
                predicted_forks = current_forks * (1 + weekly_forks_growth) ** weeks
                predictions[f'forks_{days}d'] = int(predicted_forks)
            
            # Trend sustainability prediction
            trend_strength = trend_metrics.get('trend_strength', 0.5)
            acceleration = trend_metrics.get('acceleration', {})
            stars_acceleration = acceleration.get('stars_acceleration', 0)
            
            # Calculate sustainability score (0-1)
            sustainability = trend_strength * 0.6
            if stars_acceleration > 0:
                sustainability += min(stars_acceleration * 10, 0.4)  # Positive acceleration boosts sustainability
            else:
                sustainability += max(stars_acceleration * 5, -0.2)  # Negative acceleration reduces sustainability
            
            predictions['sustainability_score'] = max(0, min(1, sustainability))
            
            # Peak prediction (when growth might slow down)
            if weekly_stars_growth > 0:
                # Simple model: growth slows when it reaches 50% weekly growth reduction
                decay_rate = 0.02  # 2% weekly decay
                weeks_to_peak = max(1, (weekly_stars_growth - 0.05) / decay_rate) if weekly_stars_growth > 0.05 else 1
                predictions['weeks_to_peak'] = int(weeks_to_peak)
                
                # Peak stars prediction
                peak_stars = current_stars * (1 + weekly_stars_growth) ** weeks_to_peak
                predictions['peak_stars'] = int(peak_stars)
            else:
                predictions['weeks_to_peak'] = 0
                predictions['peak_stars'] = current_stars
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {}
    
    def _generate_insights(self, trend_analysis: Dict[str, Any]) -> List[str]:
        """Generate insights based on trend analysis"""
        try:
            insights = []
            
            growth_patterns = trend_analysis.get('growth_patterns', {})
            trend_classification = trend_analysis.get('trend_classification', {})
            predictions = trend_analysis.get('predictions', {})
            
            # Growth pattern insights
            growth_pattern = growth_patterns.get('growth_pattern', 'unknown')
            if growth_pattern == 'explosive':
                insights.append("🚀 Explosive growth detected - project is gaining rapid traction")
            elif growth_pattern == 'high':
                insights.append("📈 High growth rate - strong upward momentum")
            elif growth_pattern == 'moderate':
                insights.append("📊 Moderate growth - steady and sustainable progress")
            elif growth_pattern == 'stagnant':
                insights.append("⏸️ Growth has stagnated - may need new features or marketing")
            elif growth_pattern == 'declining':
                insights.append("📉 Declining growth - investigate causes and consider intervention")
            
            # Momentum insights
            momentum_pattern = growth_patterns.get('momentum_pattern', 'unknown')
            if momentum_pattern == 'accelerating':
                insights.append("⚡ Accelerating momentum - growth is speeding up")
            elif momentum_pattern == 'decelerating':
                insights.append("🐌 Decelerating momentum - growth is slowing down")
            
            # Velocity insights
            velocity_pattern = growth_patterns.get('velocity_pattern', 'unknown')
            if velocity_pattern == 'high':
                insights.append("💪 High development velocity - active and productive team")
            elif velocity_pattern == 'low':
                insights.append("🐌 Low development velocity - reduced activity")
            
            # Risk insights
            risk_level = trend_classification.get('risk_level', 'unknown')
            if risk_level == 'high':
                insights.append("⚠️ High risk level - declining trends and low activity")
            elif risk_level == 'low':
                insights.append("✅ Low risk level - healthy growth patterns")
            
            # Prediction insights
            sustainability = predictions.get('sustainability_score', 0)
            if sustainability > 0.8:
                insights.append("🌱 Highly sustainable growth trend")
            elif sustainability > 0.5:
                insights.append("🔄 Moderately sustainable growth")
            else:
                insights.append("⚠️ Growth trend may not be sustainable")
            
            # Investment recommendation
            recommendation = trend_classification.get('investment_recommendation', 'unknown')
            if recommendation == 'strong_buy':
                insights.append("💎 Strong buy recommendation - excellent growth potential")
            elif recommendation == 'buy':
                insights.append("👍 Buy recommendation - good investment opportunity")
            elif recommendation == 'hold':
                insights.append("⏳ Hold recommendation - monitor for changes")
            elif recommendation == 'avoid':
                insights.append("🚫 Avoid recommendation - poor outlook")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    def _is_recent_data(self, date_str: str, days: int) -> bool:
        """Check if data is within recent days"""
        try:
            if not date_str:
                return False
            
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            days_diff = (datetime.utcnow() - date.replace(tzinfo=None)).days
            return days_diff <= days
            
        except Exception as e:
            logger.error(f"Error checking recent data: {e}")
            return False
    
    def _default_growth_rates(self) -> Dict[str, float]:
        """Default growth rates when no historical data available"""
        return {
            'stars_growth_rate': 0.01,  # 1% daily growth assumption
            'forks_growth_rate': 0.008,  # 0.8% daily growth assumption
            'contributors_growth_rate': 0.005,  # 0.5% daily growth assumption
            'weekly_stars_growth': 0.07,  # 7% weekly growth
            'weekly_forks_growth': 0.056,  # 5.6% weekly growth
            'weekly_contributors_growth': 0.035  # 3.5% weekly growth
        }
    
    def _default_trend_metrics(self) -> Dict[str, Any]:
        """Default trend metrics"""
        return {
            'stars_growth_rate': 0.0,
            'forks_growth_rate': 0.0,
            'contributors_growth_rate': 0.0,
            'weekly_stars_growth': 0.0,
            'weekly_forks_growth': 0.0,
            'weekly_contributors_growth': 0.0,
            'momentum': {},
            'velocity': {},
            'acceleration': {'stars_acceleration': 0.0, 'forks_acceleration': 0.0, 'contributors_acceleration': 0.0},
            'trend_strength': 0.5
        }
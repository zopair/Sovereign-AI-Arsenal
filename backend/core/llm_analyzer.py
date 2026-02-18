import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_config = config.get('ai_models', {})
        self.model_name = self.model_config.get('llm_model', 'gpt-4')
        self.max_tokens = self.model_config.get('max_tokens', 4000)
        self.temperature = self.model_config.get('temperature', 0.1)
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def analyze_repository(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive LLM analysis of repository"""
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return {}
            
            analysis = {
                'repo_id': repo_data.get('id'),
                'repo_name': repo_data.get('full_name'),
                'analysis_date': datetime.utcnow().isoformat(),
                'summary': {},
                'technical_analysis': {},
                'business_analysis': {},
                'innovation_potential': {},
                'recommendations': [],
                'risk_assessment': {}
            }
            
            # Extract content for analysis
            content = self._prepare_analysis_content(repo_data)
            
            # Generate different types of analysis
            analysis['summary'] = self._generate_summary(content)
            analysis['technical_analysis'] = self._analyze_technical_aspects(content)
            analysis['business_analysis'] = self._analyze_business_potential(content)
            analysis['innovation_potential'] = self._assess_innovation_potential(content)
            analysis['recommendations'] = self._generate_recommendations(content)
            analysis['risk_assessment'] = self._assess_risks(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze repository with LLM: {e}")
            return {}
    
    def _prepare_analysis_content(self, repo_data: Dict[str, Any]) -> str:
        """Prepare content for LLM analysis"""
        content_parts = []
        
        # Basic repository information
        content_parts.append(f"Repository Name: {repo_data.get('full_name', 'N/A')}")
        content_parts.append(f"Description: {repo_data.get('description', 'N/A')}")
        content_parts.append(f"Primary Language: {repo_data.get('language', 'N/A')}")
        content_parts.append(f"Stars: {repo_data.get('stargazers_count', 0)}")
        content_parts.append(f"Forks: {repo_data.get('forks_count', 0)}")
        content_parts.append(f"Open Issues: {repo_data.get('open_issues_count', 0)}")
        content_parts.append(f"Created: {repo_data.get('created_at', 'N/A')}")
        content_parts.append(f"Last Updated: {repo_data.get('updated_at', 'N/A')}")
        
        # Topics
        topics = repo_data.get('topics', [])
        if topics:
            content_parts.append(f"Topics: {', '.join(topics)}")
        
        # README content
        readme = repo_data.get('readme_content', '')
        if readme:
            # Limit README content to avoid token limits
            readme_preview = readme[:3000] if len(readme) > 3000 else readme
            content_parts.append(f"README Content:\n{readme_preview}")
        
        # Contributors info
        contributors = repo_data.get('top_contributors', [])
        if contributors:
            contributor_info = []
            for contributor in contributors[:5]:  # Top 5 contributors
                contributor_info.append(f"- {contributor.get('login', 'Unknown')}: {contributor.get('contributions', 0)} contributions")
            content_parts.append(f"Top Contributors:\n" + "\n".join(contributor_info))
        
        # Metrics
        metrics = repo_data.get('metrics', {})
        if metrics:
            content_parts.append(f"Metrics: {json.dumps(metrics, indent=2)}")
        
        return "\n\n".join(content_parts)
    
    def _generate_summary(self, content: str) -> Dict[str, Any]:
        """Generate repository summary"""
        try:
            prompt = f"""
            Analyze the following repository information and provide a comprehensive summary:

            {content}

            Please provide:
            1. A concise executive summary (2-3 sentences)
            2. Key highlights and achievements
            3. Main purpose and functionality
            4. Target audience or use cases
            5. Current maturity level (early-stage, growing, mature)

            Format your response as JSON with keys: executive_summary, highlights, purpose, target_audience, maturity_level
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
    
    def _analyze_technical_aspects(self, content: str) -> Dict[str, Any]:
        """Analyze technical aspects of the repository"""
        try:
            prompt = f"""
            Analyze the technical aspects of this repository:

            {content}

            Please provide:
            1. Technology stack assessment
            2. Code quality indicators
            3. Architecture patterns (if identifiable)
            4. Technical strengths
            5. Technical weaknesses or areas for improvement
            6. Scalability assessment
            7. Technical debt indicators

            Format your response as JSON with keys: technology_stack, code_quality, architecture, strengths, weaknesses, scalability, technical_debt
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error analyzing technical aspects: {e}")
            return {}
    
    def _analyze_business_potential(self, content: str) -> Dict[str, Any]:
        """Analyze business potential and market fit"""
        try:
            prompt = f"""
            Analyze the business potential and market fit of this repository:

            {content}

            Please provide:
            1. Market opportunity assessment
            2. Competitive landscape (if identifiable)
            3. Business model potential
            4. Market size estimate
            5. Commercial viability
            6. Target market segments
            7. Revenue potential (if applicable)

            Format your response as JSON with keys: market_opportunity, competition, business_model, market_size, viability, target_segments, revenue_potential
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error analyzing business potential: {e}")
            return {}
    
    def _assess_innovation_potential(self, content: str) -> Dict[str, Any]:
        """Assess innovation potential and uniqueness"""
        try:
            prompt = f"""
            Assess the innovation potential and uniqueness of this repository:

            {content}

            Please provide:
            1. Innovation level (breakthrough, incremental, incremental_improvement, existing_solution)
            2. Novelty aspects
            3. Technical innovation score (1-10)
            4. Market innovation score (1-10)
            5. Differentiation factors
            6. Research potential
            7. Patent or IP potential

            Format your response as JSON with keys: innovation_level, novelty, technical_innovation_score, market_innovation_score, differentiation, research_potential, ip_potential
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error assessing innovation potential: {e}")
            return {}
    
    def _generate_recommendations(self, content: str) -> List[str]:
        """Generate actionable recommendations"""
        try:
            prompt = f"""
            Based on the repository information, provide 5-7 actionable recommendations for improvement:

            {content}

            Focus on:
            1. Technical improvements
            2. Community growth
            3. Documentation enhancements
            4. Feature development
            5. Marketing and visibility
            6. Business development (if applicable)
            7. Long-term sustainability

            Format your response as a JSON array of strings, with each recommendation being concise and actionable.
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return []
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _assess_risks(self, content: str) -> Dict[str, Any]:
        """Assess potential risks"""
        try:
            prompt = f"""
            Assess potential risks for this repository:

            {content}

            Please provide:
            1. Technical risks
            2. Market risks
            3. Community risks
            4. Legal/IP risks
            5. Sustainability risks
            6. Risk level (low, medium, high)
            7. Mitigation strategies

            Format your response as JSON with keys: technical_risks, market_risks, community_risks, legal_risks, sustainability_risks, risk_level, mitigation_strategies
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error assessing risks: {e}")
            return {}
    
    def compare_repositories(self, repo1_data: Dict[str, Any], repo2_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two repositories"""
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return {}
            
            # Prepare content for both repositories
            content1 = self._prepare_analysis_content(repo1_data)
            content2 = self._prepare_analysis_content(repo2_data)
            
            prompt = f"""
            Compare the following two repositories:

            Repository 1:
            {content1}

            Repository 2:
            {content2}

            Please provide a detailed comparison covering:
            1. Technical comparison
            2. Feature comparison
            3. Community comparison
            4. Market position comparison
            5. Innovation comparison
            6. Strengths and weaknesses of each
            7. Overall recommendation

            Format your response as JSON with appropriate nested structure.
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error comparing repositories: {e}")
            return {}
    
    def generate_market_analysis(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate market analysis for multiple repositories"""
        try:
            if not self.client:
                logger.error("OpenAI client not initialized")
                return {}
            
            # Prepare summary content for all repositories
            repo_summaries = []
            for repo in repositories[:10]:  # Limit to 10 repos to avoid token limits
                summary = {
                    'name': repo.get('full_name'),
                    'description': repo.get('description'),
                    'stars': repo.get('stargazers_count', 0),
                    'language': repo.get('language'),
                    'topics': repo.get('topics', [])
                }
                repo_summaries.append(summary)
            
            content = json.dumps(repo_summaries, indent=2)
            
            prompt = f"""
            Analyze the market landscape based on these repositories:

            {content}

            Please provide:
            1. Market trends and patterns
            2. Technology trends
            3. Popular categories and niches
            4. Emerging technologies
            5. Market saturation analysis
            6. Growth opportunities
            7. Competitive dynamics

            Format your response as JSON with appropriate structure.
            """
            
            response = self._call_llm(prompt)
            if response:
                return json.loads(response)
            return {}
            
        except Exception as e:
            logger.error(f"Error generating market analysis: {e}")
            return {}
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Make API call to LLM"""
        try:
            if not self.client:
                logger.error("OpenAI client not available")
                return None
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert software analyst and business strategist. Provide detailed, accurate, and insightful analysis. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None
    
    def batch_analyze_repositories(self, repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple repositories"""
        analyses = []
        
        for repo_data in repositories:
            try:
                analysis = self.analyze_repository(repo_data)
                if analysis:
                    analyses.append(analysis)
                # Add small delay to avoid rate limits
                import time
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to analyze repository {repo_data.get('full_name', 'unknown')}: {e}")
                continue
        
        return analyses
    
    def get_analysis_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics from multiple analyses"""
        try:
            if not analyses:
                return {}
            
            summary = {
                'total_repositories': len(analyses),
                'analysis_date': datetime.utcnow().isoformat(),
                'maturity_distribution': {},
                'risk_distribution': {},
                'innovation_scores': [],
                'common_themes': [],
                'top_recommendations': []
            }
            
            # Calculate distributions
            maturity_levels = {}
            risk_levels = {}
            innovation_scores = []
            all_recommendations = []
            
            for analysis in analyses:
                # Maturity distribution
                maturity = analysis.get('summary', {}).get('maturity_level', 'unknown')
                maturity_levels[maturity] = maturity_levels.get(maturity, 0) + 1
                
                # Risk distribution
                risk = analysis.get('risk_assessment', {}).get('risk_level', 'unknown')
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
                
                # Innovation scores
                tech_score = analysis.get('innovation_potential', {}).get('technical_innovation_score', 0)
                market_score = analysis.get('innovation_potential', {}).get('market_innovation_score', 0)
                if tech_score and market_score:
                    innovation_scores.append((tech_score + market_score) / 2)
                
                # Collect recommendations
                recommendations = analysis.get('recommendations', [])
                all_recommendations.extend(recommendations)
            
            summary['maturity_distribution'] = maturity_levels
            summary['risk_distribution'] = risk_levels
            summary['innovation_scores'] = innovation_scores
            
            # Calculate average innovation score
            if innovation_scores:
                summary['average_innovation_score'] = sum(innovation_scores) / len(innovation_scores)
            
            # Get top recommendations (most common)
            from collections import Counter
            recommendation_counts = Counter(all_recommendations)
            summary['top_recommendations'] = [rec for rec, count in recommendation_counts.most_common(10)]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {}
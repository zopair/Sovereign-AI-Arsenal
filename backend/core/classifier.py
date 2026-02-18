import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from ..database.models import Classification

logger = logging.getLogger(__name__)

class RepositoryClassifier:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.categories = self._initialize_categories()
        self.ai_keywords = self._initialize_ai_keywords()
    
    def _initialize_categories(self) -> Dict[str, List[str]]:
        """Initialize repository categories and their keywords"""
        return {
            'Machine Learning': [
                'machine learning', 'ml', 'prediction', 'classification', 'regression',
                'supervised learning', 'unsupervised learning', 'ensemble', 'random forest',
                'decision tree', 'svm', 'naive bayes', 'knn', 'clustering'
            ],
            'Deep Learning': [
                'deep learning', 'neural network', 'cnn', 'rnn', 'lstm', 'gru',
                'transformer', 'attention', 'backpropagation', 'gradient descent',
                'activation function', 'dropout', 'batch normalization'
            ],
            'Computer Vision': [
                'computer vision', 'image processing', 'object detection', 'image classification',
                'segmentation', 'facial recognition', 'ocr', 'opencv', 'yolo', 'rcnn',
                'image generation', 'style transfer', 'gans', 'vae'
            ],
            'Natural Language Processing': [
                'natural language processing', 'nlp', 'text processing', 'sentiment analysis',
                'text classification', 'named entity recognition', 'pos tagging', 'tokenization',
                'word embedding', 'bert', 'gpt', 'transformer', 'language model'
            ],
            'Reinforcement Learning': [
                'reinforcement learning', 'rl', 'q-learning', 'policy gradient', 'actor critic',
                'dqn', 'a3c', 'ppo', 'monte carlo', 'temporal difference', 'reward',
                'environment', 'agent', 'policy', 'value function'
            ],
            'Data Science': [
                'data science', 'data analysis', 'analytics', 'visualization', 'pandas',
                'numpy', 'matplotlib', 'seaborn', 'plotly', 'dashboard', 'statistics',
                'hypothesis testing', 'a/b testing', 'feature engineering'
            ],
            'MLOps': [
                'mlops', 'machine learning operations', 'model deployment', 'kubernetes',
                'docker', 'ci/cd', 'model monitoring', 'experiment tracking', 'mlflow',
                'kubeflow', 'airflow', 'pipeline', 'automation', 'scaling'
            ],
            'AI Framework': [
                'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'xgboost', 'lightgbm',
                'caffe', 'mxnet', 'theano', 'chainer', 'fastai', 'huggingface',
                'spacy', 'nltk', 'gensim', 'jupyter', 'colab'
            ],
            'Generative AI': [
                'generative ai', 'gan', 'vae', 'diffusion model', 'stable diffusion',
                'dall-e', 'midjourney', 'image generation', 'text generation', 'stylegan',
                'cycle gan', 'pix2pix', 'deepfake', 'synthetic data'
            ],
            'Large Language Models': [
                'large language model', 'llm', 'gpt', 'bert', 't5', 'llama', 'alpaca',
                'chatbot', 'conversational ai', 'prompt engineering', 'fine-tuning',
                'inference', 'embedding', 'tokenization', 'attention mechanism'
            ],
            'Robotics': [
                'robotics', 'robot', 'autonomous vehicle', 'self-driving', 'drone',
                'robot arm', 'path planning', 'slam', 'control theory', 'kinematics',
                'ros', 'robot operating system', 'computer vision', 'sensor fusion'
            ],
            'AI Ethics': [
                'ai ethics', 'responsible ai', 'fairness', 'bias', 'interpretability',
                'explainable ai', 'xai', 'transparency', 'accountability', 'privacy',
                'security', 'robustness', 'safety', 'human-centered ai'
            ]
        }
    
    def _initialize_ai_keywords(self) -> Dict[str, float]:
        """Initialize AI-related keywords with relevance scores"""
        return {
            # High relevance (0.9-1.0)
            'artificial intelligence': 1.0, 'machine learning': 1.0, 'deep learning': 1.0,
            'neural network': 1.0, 'transformer': 0.95, 'attention': 0.95,
            
            # Medium-high relevance (0.7-0.9)
            'tensorflow': 0.9, 'pytorch': 0.9, 'keras': 0.85, 'scikit-learn': 0.85,
            'nlp': 0.85, 'computer vision': 0.85, 'reinforcement learning': 0.85,
            
            # Medium relevance (0.5-0.7)
            'ai': 0.7, 'ml': 0.7, 'automation': 0.6, 'chatbot': 0.65,
            'prediction': 0.6, 'classification': 0.6, 'clustering': 0.6,
            
            # Low-medium relevance (0.3-0.5)
            'data science': 0.5, 'analytics': 0.4, 'visualization': 0.4,
            'statistics': 0.4, 'algorithm': 0.4, 'optimization': 0.4,
            
            # Low relevance (0.1-0.3)
            'python': 0.2, 'jupyter': 0.2, 'docker': 0.15, 'api': 0.15,
            'web': 0.1, 'app': 0.1, 'tool': 0.1, 'library': 0.2
        }
    
    def classify_repository(self, repo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Classify repository into categories"""
        try:
            classifications = []
            
            # Extract text content from repository
            text_content = self._extract_text_content(repo_data)
            
            # Calculate category scores
            category_scores = self._calculate_category_scores(text_content)
            
            # Get top categories
            top_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Create classification objects
            for category, score in top_categories:
                if score > 0.1:  # Minimum threshold
                    classification = {
                        'category': category,
                        'confidence': score,
                        'subcategory': self._get_subcategory(category, text_content),
                        'tags': self._extract_tags(category, text_content),
                        'reasoning': self._generate_reasoning(category, score, text_content),
                        'model_version': 'v1.0',
                        'created_at': datetime.utcnow().isoformat()
                    }
                    classifications.append(classification)
            
            # Limit to top 5 categories
            classifications = classifications[:5]
            
            logger.info(f"Classified repository {repo_data.get('full_name')} into {len(classifications)} categories")
            return classifications
            
        except Exception as e:
            logger.error(f"Failed to classify repository: {e}")
            return []
    
    def _extract_text_content(self, repo_data: Dict[str, Any]) -> str:
        """Extract all text content from repository for classification"""
        text_parts = []
        
        # Basic repository info
        text_parts.append(repo_data.get('name', ''))
        text_parts.append(repo_data.get('description', ''))
        text_parts.append(repo_data.get('language', ''))
        
        # Topics
        topics = repo_data.get('topics', [])
        text_parts.extend(topics)
        
        # README content
        readme = repo_data.get('readme_content', '')
        if readme:
            # Clean README content (remove markdown, URLs, etc.)
            cleaned_readme = self._clean_text(readme)
            text_parts.append(cleaned_readme)
        
        # Combine all text
        combined_text = ' '.join(text_parts).lower()
        return combined_text
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing markdown, URLs, and special characters"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove markdown headers
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Remove markdown code blocks
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _calculate_category_scores(self, text_content: str) -> Dict[str, float]:
        """Calculate relevance scores for each category"""
        category_scores = {}
        
        for category, keywords in self.categories.items():
            score = 0.0
            keyword_matches = 0
            
            for keyword in keywords:
                keyword_count = text_content.count(keyword)
                if keyword_count > 0:
                    # Get keyword relevance weight
                    keyword_weight = self.ai_keywords.get(keyword, 0.5)
                    score += keyword_count * keyword_weight
                    keyword_matches += 1
            
            # Normalize score by number of keywords and text length
            if keyword_matches > 0:
                # Score normalization: (matches / total_keywords) * (keyword_weight_sum / matches)
                match_ratio = keyword_matches / len(keywords)
                normalized_score = match_ratio * min(score / len(text_content.split()), 1.0)
                category_scores[category] = normalized_score
            else:
                category_scores[category] = 0.0
        
        return category_scores
    
    def _get_subcategory(self, category: str, text_content: str) -> Optional[str]:
        """Determine subcategory based on content"""
        subcategory_mapping = {
            'Machine Learning': {
                'supervised': ['supervised', 'classification', 'regression', 'prediction'],
                'unsupervised': ['unsupervised', 'clustering', 'dimensionality reduction', 'anomaly'],
                'ensemble': ['ensemble', 'random forest', 'boosting', 'bagging']
            },
            'Deep Learning': {
                'cnn': ['cnn', 'convolutional', 'image', 'vision'],
                'rnn': ['rnn', 'recurrent', 'sequence', 'time series'],
                'transformer': ['transformer', 'attention', 'bert', 'gpt'],
                'gan': ['gan', 'generative', 'adversarial', 'vae']
            },
            'Computer Vision': {
                'detection': ['detection', 'object', 'yolo', 'rcnn'],
                'segmentation': ['segmentation', 'mask', 'pixel'],
                'recognition': ['recognition', 'face', 'biometric'],
                'generation': ['generation', 'synthetic', 'style transfer']
            },
            'Natural Language Processing': {
                'text_classification': ['text classification', 'sentiment', 'categorization'],
                'ner': ['named entity', 'ner', 'entity recognition'],
                'translation': ['translation', 'machine translation'],
                'generation': ['text generation', 'language generation', 'dialogue']
            }
        }
        
        if category not in subcategory_mapping:
            return None
        
        subcategories = subcategory_mapping[category]
        best_subcategory = None
        best_score = 0.0
        
        for subcat, keywords in subcategories.items():
            score = sum(text_content.count(keyword) for keyword in keywords)
            if score > best_score:
                best_score = score
                best_subcategory = subcat
        
        return best_subcategory if best_score > 0 else None
    
    def _extract_tags(self, category: str, text_content: str) -> List[str]:
        """Extract relevant tags for the category"""
        # Get category keywords
        category_keywords = self.categories.get(category, [])
        
        # Find keywords that appear in text
        tags = []
        for keyword in category_keywords:
            if keyword in text_content:
                tags.append(keyword)
        
        # Add technology-specific tags
        tech_tags = {
            'python': 'python',
            'tensorflow': 'tensorflow',
            'pytorch': 'pytorch',
            'keras': 'keras',
            'scikit-learn': 'scikit-learn',
            'jupyter': 'jupyter',
            'docker': 'docker',
            'kubernetes': 'kubernetes',
            'aws': 'aws',
            'gcp': 'gcp',
            'azure': 'azure'
        }
        
        for tech, tag in tech_tags.items():
            if tech in text_content and tag not in tags:
                tags.append(tag)
        
        return tags[:10]  # Limit to 10 tags
    
    def _generate_reasoning(self, category: str, score: float, text_content: str) -> str:
        """Generate reasoning for classification"""
        category_keywords = self.categories.get(category, [])
        found_keywords = [kw for kw in category_keywords if kw in text_content]
        
        if not found_keywords:
            return f"Low confidence match based on general patterns"
        
        top_keywords = found_keywords[:3]
        keyword_str = ", ".join(top_keywords)
        
        if len(found_keywords) == 1:
            return f"Strong match due to presence of '{keyword_str}'"
        elif len(found_keywords) <= 3:
            return f"Good match based on keywords: {keyword_str}"
        else:
            return f"Excellent match with multiple keywords: {keyword_str} and {len(found_keywords) - 3} others"
    
    def batch_classify_repositories(self, repositories: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Classify multiple repositories"""
        all_classifications = []
        
        for repo_data in repositories:
            try:
                classifications = self.classify_repository(repo_data)
                all_classifications.append(classifications)
            except Exception as e:
                logger.error(f"Failed to classify repository {repo_data.get('full_name', 'unknown')}: {e}")
                all_classifications.append([])
        
        return all_classifications
    
    def get_category_statistics(self, classifications: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get statistics about category distributions"""
        category_counts = {}
        total_repos = len(classifications)
        
        for repo_classifications in classifications:
            categories_seen = set()
            for classification in repo_classifications:
                category = classification.get('category')
                if category and category not in categories_seen:
                    categories_seen.add(category)
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate percentages
        category_stats = {}
        for category, count in category_counts.items():
            category_stats[category] = {
                'count': count,
                'percentage': (count / total_repos) * 100 if total_repos > 0 else 0
            }
        
        return {
            'total_repositories': total_repos,
            'category_distribution': category_stats,
            'most_common_category': max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        }
"""
Google Colab compatibility module for Sovereign AI Arsenal

This module provides compatibility layer for running the platform in Google Colab notebooks.
It handles environment detection, dependency installation, and resource management.
"""

import os
import sys
import subprocess
import logging
import asyncio
import json
import warnings
from typing import Dict, Any, List, Optional
from pathlib import Path
import importlib.util

logger = logging.getLogger(__name__)

class ColabEnvironment:
    """Google Colab environment detection and management"""
    
    @staticmethod
    def is_colab() -> bool:
        """Check if running in Google Colab"""
        try:
            import google.colab
            return True
        except ImportError:
            return False
    
    @staticmethod
    def detect_environment() -> Dict[str, Any]:
        """Detect current environment and capabilities"""
        env_info = {
            'is_colab': ColabEnvironment.is_colab(),
            'python_version': sys.version,
            'platform': sys.platform,
            'gpu_available': False,
            'tpu_available': False,
            'memory_gb': 0,
            'cpu_cores': 0,
            'disk_space_gb': 0
        }
        
        try:
            # Check for GPU
            if env_info['is_colab']:
                try:
                    import torch
                    env_info['gpu_available'] = torch.cuda.is_available()
                    if env_info['gpu_available']:
                        env_info['gpu_name'] = torch.cuda.get_device_name(0)
                        env_info['gpu_memory_gb'] = torch.cuda.get_device_properties(0).total_memory / 1e9
                except ImportError:
                    pass
                
                # Check for TPU
                try:
                    import jax
                    env_info['tpu_available'] = len(jax.devices()) > 0
                except ImportError:
                    pass
            
            # Get system info
            import psutil
            env_info['memory_gb'] = psutil.virtual_memory().total / 1e9
            env_info['cpu_cores'] = psutil.cpu_count()
            env_info['disk_space_gb'] = psutil.disk_usage('/').free / 1e9
            
        except Exception as e:
            logger.warning(f"Error detecting environment: {e}")
        
        return env_info

class ColabDependencyManager:
    """Manage dependencies for Colab environment"""
    
    def __init__(self):
        self.installed_packages = set()
        self.required_packages = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2-binary',
            'aiohttp', 'aiofiles', 'pydantic', 'pyyaml', 'python-dotenv',
            'pandas', 'numpy', 'scikit-learn', 'openai', 'chromadb',
            'sentence-transformers', 'docker', 'redis', 'prometheus-client'
        ]
    
    def install_dependencies(self, force_reinstall: bool = False) -> bool:
        """Install required dependencies in Colab"""
        if not ColabEnvironment.is_colab():
            return True
        
        try:
            # Install system dependencies
            system_packages = ['git', 'curl', 'wget']
            for package in system_packages:
                try:
                    subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
                    subprocess.run(['apt-get', 'install', '-y', package], check=True, capture_output=True)
                    logger.info(f"Installed system package: {package}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to install {package}: {e}")
            
            # Install Python packages
            for package in self.required_packages:
                if force_reinstall or package not in self.installed_packages:
                    try:
                        subprocess.run([
                            sys.executable, '-m', 'pip', 'install', package, '--quiet'
                        ], check=True, capture_output=True)
                        self.installed_packages.add(package)
                        logger.info(f"Installed Python package: {package}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to install {package}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def check_docker_availability(self) -> bool:
        """Check if Docker is available in Colab"""
        if not ColabEnvironment.is_colab():
            return True
        
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

class ColabDatabaseManager:
    """Manage database connections for Colab environment"""
    
    def __init__(self):
        self.use_sqlite = False
        self.connection_string = None
    
    def setup_database(self, force_sqlite: bool = False) -> str:
        """Setup database for Colab environment"""
        if ColabEnvironment.is_colab() or force_sqlite:
            # Use SQLite for Colab (no external database needed)
            self.use_sqlite = True
            self.connection_string = 'sqlite:///colab_sovereign_ai_arsenal.db'
            logger.info("Using SQLite database for Colab environment")
        else:
            # Use PostgreSQL (default)
            self.connection_string = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/sovereign ai arsenal')
            logger.info("Using PostgreSQL database")
        
        return self.connection_string
    
    def create_sqlite_engine(self, connection_string: str):
        """Create SQLite engine with proper configuration"""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import StaticPool
        
        engine = create_engine(
            connection_string,
            connect_args={
                'check_same_thread': False,
                'timeout': 20
            },
            poolclass=StaticPool,
            echo=False
        )
        return engine

class ColabVectorStore:
    """Vector store optimized for Colab environment"""
    
    def __init__(self):
        self.use_in_memory = False
        self.persist_directory = None
    
    def setup_vector_store(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup vector store for Colab environment"""
        if ColabEnvironment.is_colab():
            # Use in-memory vector store for Colab
            self.use_in_memory = True
            self.persist_directory = '/tmp/colab_vectors'
            
            colab_config = {
                'provider': 'chromadb',
                'collection_name': 'colab_ai_repositories',
                'persist_directory': self.persist_directory,
                'in_memory': True
            }
            
            # Update config
            config.update(colab_config)
            logger.info("Using in-memory vector store for Colab")
        
        return config

class ColabSandboxManager:
    """Simplified sandbox manager for Colab environment"""
    
    def __init__(self):
        self.docker_available = False
        self.use_local_execution = False
    
    def setup_sandbox(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup sandbox for Colab environment"""
        if ColabEnvironment.is_colab():
            # Check if Docker is available
            dependency_manager = ColabDependencyManager()
            self.docker_available = dependency_manager.check_docker_availability()
            
            if not self.docker_available:
                # Use local execution without Docker
                self.use_local_execution = True
                colab_config = {
                    'use_docker': False,
                    'timeout': 60,  # Shorter timeout for Colab
                    'max_file_size': 10 * 1024 * 1024,  # 10MB limit
                    'enable_security_scan': False  # Skip security scan for performance
                }
                
                config.get('sandbox', {}).update(colab_config)
                logger.info("Using local execution for Colab (no Docker)")
            else:
                logger.info("Docker available in Colab, using sandbox")
        
        return config
    
    async def analyze_repository_locally(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository locally without Docker"""
        if not self.use_local_execution:
            return {}
        
        try:
            from pathlib import Path
            import tempfile
            import shutil
            import subprocess
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                repo_name = repo_data.get('full_name', '').replace('/', '_')
                repo_path = temp_path / repo_name
                
                # Clone repository
                clone_cmd = [
                    'git', 'clone', '--depth', '1', '--single-branch',
                    repo_data.get('clone_url', ''), str(repo_path)
                ]
                
                result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)
                
                analysis_result = {
                    'repository_id': str(repo_data.get('id', '')),
                    'clone_success': result.returncode == 0,
                    'install_success': False,
                    'test_success': False,
                    'setup_complexity_score': 0.5,  # Default score
                    'execution_time_seconds': 0.0,
                    'error_logs': [result.stderr] if result.stderr else [],
                    'test_output': '',
                    'dependencies': [],
                    'file_structure': {},
                    'security_issues': [],
                    'performance_metrics': {},
                    'sandbox_metadata': {
                        'environment': 'colab_local',
                        'docker_used': False
                    }
                }
                
                if result.returncode == 0:
                    # Analyze file structure
                    analysis_result['file_structure'] = self._analyze_files(repo_path)
                    
                    # Look for requirements
                    requirements_file = repo_path / 'requirements.txt'
                    if requirements_file.exists():
                        try:
                            with open(requirements_file, 'r') as f:
                                requirements = f.read()
                            analysis_result['dependencies'] = [
                                line.strip() for line in requirements.split('\n')
                                if line.strip() and not line.startswith('#')
                            ]
                        except Exception as e:
                            analysis_result['error_logs'].append(f"Error reading requirements: {e}")
                
                return analysis_result
                
        except Exception as e:
            logger.error(f"Error in local repository analysis: {e}")
            return {
                'repository_id': str(repo_data.get('id', '')),
                'clone_success': False,
                'error_logs': [f"Local analysis error: {str(e)}"],
                'setup_complexity_score': 0.8,  # High complexity due to error
                'sandbox_metadata': {'environment': 'colab_local_error'}
            }
    
    def _analyze_files(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze file structure"""
        structure = {
            'total_files': 0,
            'total_size': 0,
            'languages': {},
            'config_files': [],
            'test_files': []
        }
        
        try:
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    structure['total_files'] += 1
                    structure['total_size'] += file_path.stat().st_size
                    
                    ext = file_path.suffix.lower()
                    if ext:
                        structure['languages'][ext] = structure['languages'].get(ext, 0) + 1
                    
                    if 'requirements' in file_path.name or 'setup' in file_path.name:
                        structure['config_files'].append(str(file_path.name))
                    elif 'test' in file_path.name:
                        structure['test_files'].append(str(file_path.name))
        
        except Exception as e:
            logger.error(f"Error analyzing files: {e}")
        
        return structure

class ColabIntegration:
    """Main integration class for Colab compatibility"""
    
    def __init__(self):
        self.env_info = ColabEnvironment.detect_environment()
        self.dependency_manager = ColabDependencyManager()
        self.database_manager = ColabDatabaseManager()
        self.vector_store = ColabVectorStore()
        self.sandbox_manager = ColabSandboxManager()
        
        # Suppress warnings in Colab
        if self.env_info['is_colab']:
            warnings.filterwarnings('ignore')
    
    def setup_environment(self, force_sqlite: bool = False) -> Dict[str, Any]:
        """Setup complete environment for Colab"""
        setup_info = {
            'environment': 'colab' if self.env_info['is_colab'] else 'standard',
            'setup_success': False,
            'components': {}
        }
        
        try:
            if self.env_info['is_colab']:
                logger.info("Setting up Colab environment...")
                
                # Install dependencies
                if not self.dependency_manager.install_dependencies():
                    raise Exception("Failed to install dependencies")
                
                setup_info['components']['dependencies'] = 'installed'
                
                # Setup database
                connection_string = self.database_manager.setup_database(force_sqlite)
                setup_info['components']['database'] = 'sqlite' if self.database_manager.use_sqlite else 'postgresql'
                
                # Setup vector store
                vector_config = self.vector_store.setup_vector_store({})
                setup_info['components']['vector_store'] = 'in_memory' if self.vector_store.use_in_memory else 'persistent'
                
                # Setup sandbox
                sandbox_config = self.sandbox_manager.setup_sandbox({})
                setup_info['components']['sandbox'] = 'local' if self.sandbox_manager.use_local_execution else 'docker'
                
                setup_info['setup_success'] = True
                logger.info("Colab environment setup completed successfully")
                
            else:
                logger.info("Standard environment detected, no special setup needed")
                setup_info['components'] = {'database': 'postgresql', 'vector_store': 'persistent', 'sandbox': 'docker'}
                setup_info['setup_success'] = True
        
        except Exception as e:
            logger.error(f"Error setting up Colab environment: {e}")
            setup_info['error'] = str(e)
        
        return setup_info
    
    def create_colab_config(self) -> Dict[str, Any]:
        """Create configuration optimized for Colab"""
        config = {
            'app_name': 'Sovereign AI Arsenal - Colab',
            'environment': 'colab',
            'database': {
                'url': self.database_manager.connection_string,
                'use_sqlite': self.database_manager.use_sqlite
            },
            'vector_store': {
                'use_in_memory': self.vector_store.use_in_memory,
                'persist_directory': self.vector_store.persist_directory
            },
            'sandbox': {
                'use_docker': not self.sandbox_manager.use_local_execution,
                'timeout': 60,
                'enable_security_scan': False
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'debug': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        return config
    
    async def test_integration(self) -> Dict[str, Any]:
        """Test Colab integration"""
        test_results = {
            'environment_test': self.env_info,
            'dependency_test': False,
            'database_test': False,
            'vector_store_test': False,
            'api_test': False
        }
        
        try:
            # Test dependencies
            try:
                import fastapi, sqlalchemy, pandas, numpy
                test_results['dependency_test'] = True
            except ImportError as e:
                test_results['dependency_error'] = str(e)
            
            # Test database
            try:
                if self.database_manager.use_sqlite:
                    from sqlalchemy import create_engine
                    engine = self.database_manager.create_sqlite_engine(self.database_manager.connection_string)
                    with engine.connect() as conn:
                        conn.execute("SELECT 1")
                    test_results['database_test'] = True
            except Exception as e:
                test_results['database_error'] = str(e)
            
            # Test vector store
            try:
                import chromadb
                if self.vector_store.use_in_memory:
                    client = chromadb.Client()
                    test_results['vector_store_test'] = True
                else:
                    # Test persistent store (if available)
                    pass
            except Exception as e:
                test_results['vector_store_error'] = str(e)
            
            # Test API
            try:
                from fastapi import FastAPI
                app = FastAPI()
                test_results['api_test'] = True
            except Exception as e:
                test_results['api_error'] = str(e)
        
        except Exception as e:
            test_results['general_error'] = str(e)
        
        return test_results

# Colab-specific utility functions
def install_colab_dependencies():
    """Install dependencies for Colab environment"""
    colab = ColabIntegration()
    return colab.dependency_manager.install_dependencies()

def setup_colab_environment(force_sqlite: bool = False):
    """Setup Colab environment"""
    colab = ColabIntegration()
    return colab.setup_environment(force_sqlite)

def run_in_colab(func):
    """Decorator to run function in Colab-compatible mode"""
    def wrapper(*args, **kwargs):
        if ColabEnvironment.is_colab():
            # Setup Colab environment
            colab = ColabIntegration()
            setup_result = colab.setup_environment()
            
            if not setup_result['setup_success']:
                raise Exception(f"Colab setup failed: {setup_result.get('error', 'Unknown error')}")
            
            # Update kwargs with Colab config
            kwargs['colab_config'] = colab.create_colab_config()
        
        return func(*args, **kwargs)
    return wrapper

# Colab notebook helper
def create_colab_notebook_template():
    """Create a template for Colab notebook"""
    template = '''
# Sovereign AI Arsenal - Google Colab Notebook

## Installation
```python
# Install dependencies
!pip install fastapi uvicorn sqlalchemy pandas numpy scikit-learn openai chromadb sentence-transformers

# Clone repository (if needed)
!git clone https://github.com/your-repo/sovereign-ai-arsenal.git
%cd sovereign-ai-arsenal/backend
```

## Setup
```python
from colab_integration import ColabIntegration, setup_colab_environment

# Setup Colab environment
setup_result = setup_colab_environment()
print("Setup result:", setup_result)
```

## Basic Usage
```python
# Import modules
from core.discovery import GitHubDiscoveryEngine
from core.evaluator import RepositoryEvaluator
import asyncio

# Example: Discover repositories
async def discover_example():
    config = {
        'github': {
            'token': 'your-github-token'  # Set this in Colab secrets
        }
    }
    
    engine = GitHubDiscoveryEngine(config['github'])
    repos = await engine.discover_ai_repositories(
        queries=["machine learning"], 
        max_repos_per_query=5
    )
    
    print(f"Found {len(repos)} repositories")
    return repos

# Run the example
repos = await discover_example()
```

## Visualization
```python
import pandas as pd
import matplotlib.pyplot as plt

# Create DataFrame from repositories
df = pd.DataFrame([{
    'name': repo['name'],
    'stars': repo['stargazers_count'],
    'language': repo['language']
} for repo in repos])

# Plot stars by language
df.groupby('language')['stars'].sum().plot(kind='bar')
plt.title('Stars by Programming Language')
plt.ylabel('Total Stars')
plt.xticks(rotation=45)
plt.show()
```
'''
    
    return template

# Auto-detect and setup when imported
if ColabEnvironment.is_colab():
    logger.info("Colab environment detected, setting up compatibility mode...")
    colab_integration = ColabIntegration()
    setup_result = colab_integration.setup_environment()
    
    if setup_result['setup_success']:
        logger.info("Colab compatibility setup completed")
    else:
        logger.warning(f"Colab setup issues: {setup_result.get('error', 'Unknown error')}")
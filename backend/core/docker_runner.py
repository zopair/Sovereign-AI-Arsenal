import asyncio
import aiofiles
import aiohttp
import logging
import docker
import json
import os
import tempfile
import shutil
import re
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import tarfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SandboxResult:
    """Result from sandbox execution"""
    repository_id: str
    clone_success: bool
    install_success: bool
    test_success: bool
    setup_complexity_score: float
    execution_time_seconds: float
    error_logs: List[str]
    test_output: str
    dependencies: List[str]
    file_structure: Dict[str, Any]
    security_issues: List[str]
    performance_metrics: Dict[str, Any]
    sandbox_metadata: Dict[str, Any]

class DockerSandboxManager:
    """Manages Docker sandbox execution for repository analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sandbox_config = config.get('sandbox', {})
        self.docker_client = None
        self.image_name = self.sandbox_config.get('base_image', 'python:3.11-slim')
        self.timeout = self.sandbox_config.get('timeout', 300)  # 5 minutes
        self.max_file_size = self.sandbox_config.get('max_file_size', 50 * 1024 * 1024)  # 50MB
        self.memory_limit = self.sandbox_config.get('memory_limit', '512m')
        self.cpu_limit = self.sandbox_config.get('cpu_limit', '1.0')
        
        # Security settings
        self.allowed_domains = self.sandbox_config.get('allowed_domains', [
            'github.com', 'pypi.org', 'files.pythonhosted.org'
        ])
        self.blocked_commands = self.sandbox_config.get('blocked_commands', [
            'rm -rf', 'sudo', 'chmod 777', 'systemctl', 'service'
        ])
        
        self._initialize_docker()
    
    def _initialize_docker(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            # Test daemon connectivity before attempting any image operations.
            self.docker_client.ping()

            # Ensure the configured execution image exists locally.
            try:
                self.docker_client.images.get(self.image_name)
                logger.info("Sandbox image already available: %s", self.image_name)
            except docker.errors.ImageNotFound:
                logger.info("Pulling missing sandbox image: %s", self.image_name)
                self.docker_client.images.pull(self.image_name)

            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
    
    async def analyze_repository_in_sandbox(self, repo_data: Dict[str, Any]) -> SandboxResult:
        """Complete repository analysis in Docker sandbox"""
        start_time = datetime.utcnow()
        repo_id = str(repo_data.get('id', ''))
        clone_url = repo_data.get('clone_url', '')
        repo_name = repo_data.get('full_name', '').replace('/', '_')
        
        logger.info(f"Starting sandbox analysis for repository: {repo_name}")
        
        # Initialize result
        result = SandboxResult(
            repository_id=repo_id,
            clone_success=False,
            install_success=False,
            test_success=False,
            setup_complexity_score=0.0,
            execution_time_seconds=0.0,
            error_logs=[],
            test_output="",
            dependencies=[],
            file_structure={},
            security_issues=[],
            performance_metrics={},
            sandbox_metadata={}
        )
        
        try:
            # Create temporary workspace
            with tempfile.TemporaryDirectory() as workspace:
                workspace_path = Path(workspace)
                
                # Step 1: Clone repository
                clone_result = await self._clone_repository(clone_url, workspace_path, repo_name)
                result.clone_success = clone_result['success']
                result.error_logs.extend(clone_result.get('errors', []))
                
                if not result.clone_success:
                    logger.error(f"Failed to clone repository: {repo_name}")
                    return result
                
                repo_path = workspace_path / repo_name
                
                # Step 2: Analyze file structure
                result.file_structure = await self._analyze_file_structure(repo_path)
                
                # Step 3: Security scan
                result.security_issues = await self._security_scan(repo_path)
                
                # Step 4: Install dependencies
                install_result = await self._install_dependencies(repo_path)
                result.install_success = install_result['success']
                result.dependencies = install_result.get('dependencies', [])
                result.error_logs.extend(install_result.get('errors', []))
                
                # Step 5: Run tests
                test_result = await self._run_tests(repo_path)
                result.test_success = test_result['success']
                result.test_output = test_result.get('output', '')
                result.error_logs.extend(test_result.get('errors', []))
                
                # Step 6: Calculate setup complexity score
                result.setup_complexity_score = await self._calculate_setup_complexity_score(
                    result, repo_data
                )
                
                # Step 7: Performance metrics
                result.performance_metrics = await self._collect_performance_metrics(repo_path)
                
                # Step 8: Sandbox metadata
                result.sandbox_metadata = {
                    'workspace_size': self._get_directory_size(workspace_path),
                    'container_id': None,  # Will be set if container was used
                    'execution_time': str(datetime.utcnow() - start_time),
                    'docker_image': self.image_name
                }
                
        except Exception as e:
            logger.error(f"Error in sandbox analysis for {repo_name}: {e}")
            result.error_logs.append(f"Sandbox execution error: {str(e)}")
        
        finally:
            result.execution_time_seconds = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Sandbox analysis completed for {repo_name} in {result.execution_time_seconds:.2f}s")
        
        return result
    
    async def _clone_repository(self, clone_url: str, workspace_path: Path, repo_name: str) -> Dict[str, Any]:
        """Clone repository using git"""
        result = {'success': False, 'errors': []}
        
        try:
            # Security check URL
            if not self._is_safe_url(clone_url):
                result['errors'].append(f"Unsafe clone URL: {clone_url}")
                return result
            
            # Clone with depth limit and timeout
            clone_cmd = [
                'git', 'clone',
                '--depth', '1',  # Shallow clone for speed
                '--single-branch',
                clone_url,
                str(workspace_path / repo_name)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workspace_path)
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            
            if process.returncode == 0:
                result['success'] = True
                logger.info(f"Successfully cloned repository: {repo_name}")
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                result['errors'].append(f"Clone failed: {error_msg}")
                logger.error(f"Failed to clone {repo_name}: {error_msg}")
        
        except asyncio.TimeoutError:
            result['errors'].append("Clone operation timed out")
        except Exception as e:
            result['errors'].append(f"Clone error: {str(e)}")
        
        return result
    
    async def _analyze_file_structure(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze repository file structure"""
        structure = {
            'total_files': 0,
            'total_size': 0,
            'languages': {},
            'config_files': [],
            'test_files': [],
            'documentation_files': [],
            'directories': [],
            'suspicious_files': []
        }
        
        try:
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    # Skip hidden files and very large files
                    if file_path.name.startswith('.') or file_path.stat().st_size > self.max_file_size:
                        continue
                    
                    structure['total_files'] += 1
                    structure['total_size'] += file_path.stat().st_size
                    
                    # File extension analysis
                    ext = file_path.suffix.lower()
                    if ext:
                        structure['languages'][ext] = structure['languages'].get(ext, 0) + 1
                    
                    # Special file detection
                    file_name = file_path.name.lower()
                    if file_name in ['requirements.txt', 'package.json', 'setup.py', 'pyproject.toml', 'environment.yml']:
                        structure['config_files'].append(str(file_path.relative_to(repo_path)))
                    elif 'test' in file_name or file_path.parent.name.lower() in ['tests', 'test']:
                        structure['test_files'].append(str(file_path.relative_to(repo_path)))
                    elif file_name in ['readme.md', 'readme.rst', 'doc', 'docs']:
                        structure['documentation_files'].append(str(file_path.relative_to(repo_path)))
                    elif file_name in ['.env', 'config.json', 'secrets.txt', 'private.key']:
                        structure['suspicious_files'].append(str(file_path.relative_to(repo_path)))
                
                elif file_path.is_dir() and not file_path.name.startswith('.'):
                    structure['directories'].append(str(file_path.relative_to(repo_path)))
        
        except Exception as e:
            logger.error(f"Error analyzing file structure: {e}")
        
        return structure
    
    async def _security_scan(self, repo_path: Path) -> List[str]:
        """Basic security scan of repository"""
        issues = []
        
        try:
            # Scan for suspicious files
            suspicious_patterns = [
                r'password',
                r'secret',
                r'key',
                r'token',
                r'credential',
                r'\.env',
                r'private',
                r'auth'
            ]
            
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        # Check filename
                        file_name = file_path.name.lower()
                        for pattern in suspicious_patterns:
                            if re.search(pattern, file_name):
                                issues.append(f"Suspicious filename: {file_path.relative_to(repo_path)}")
                                break
                        
                        # Check file content (only for text files)
                        if file_path.suffix in ['.py', '.js', '.json', '.yaml', '.yml', '.env', '.txt']:
                            try:
                                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                    content = await f.read()
                                    for pattern in suspicious_patterns:
                                        if re.search(pattern, content, re.IGNORECASE):
                                            issues.append(f"Suspicious content in: {file_path.relative_to(repo_path)}")
                                            break
                            except UnicodeDecodeError:
                                # Skip binary files
                                pass
                    except Exception as e:
                        logger.debug(f"Error scanning file {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error in security scan: {e}")
            issues.append(f"Security scan error: {str(e)}")
        
        return issues
    
    async def _install_dependencies(self, repo_path: Path) -> Dict[str, Any]:
        """Install repository dependencies"""
        result = {'success': False, 'dependencies': [], 'errors': []}
        
        try:
            # Check for different package managers
            requirements_files = [
                repo_path / 'requirements.txt',
                repo_path / 'setup.py',
                repo_path / 'pyproject.toml',
                repo_path / 'environment.yml',
                repo_path / 'Pipfile'
            ]
            
            install_cmd = None
            dependencies = []
            
            # Python requirements.txt
            if (repo_path / 'requirements.txt').exists():
                install_cmd = ['pip', 'install', '-r', 'requirements.txt']
                async with aiofiles.open(repo_path / 'requirements.txt', 'r') as f:
                    content = await f.read()
                    dependencies = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            
            # setup.py
            elif (repo_path / 'setup.py').exists():
                install_cmd = ['pip', 'install', '-e', '.']
                # Try to extract dependencies from setup.py
                try:
                    async with aiofiles.open(repo_path / 'setup.py', 'r') as f:
                        content = await f.read()
                        # Simple regex to extract install_requires
                        matches = re.findall(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
                        for match in matches:
                            deps = re.findall(r'["\']([^"\']+)["\']', match)
                            dependencies.extend(deps)
                except Exception as e:
                    logger.debug(f"Error parsing setup.py: {e}")
            
            # pyproject.toml
            elif (repo_path / 'pyproject.toml').exists():
                install_cmd = ['pip', 'install', '-e', '.']
                try:
                    async with aiofiles.open(repo_path / 'pyproject.toml', 'r') as f:
                        content = await f.read()
                        # Simple extraction of dependencies
                        if 'dependencies' in content:
                            matches = re.findall(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
                            for match in matches:
                                deps = re.findall(r'["\']([^"\']+)["\']', match)
                                dependencies.extend(deps)
                except Exception as e:
                    logger.debug(f"Error parsing pyproject.toml: {e}")
            
            if not install_cmd:
                result['success'] = True  # No dependencies to install
                result['dependencies'] = dependencies
                return result
            
            # Run installation in Docker container for security
            container = None
            try:
                # Create container
                container = self.docker_client.containers.create(
                    image=self.image_name,
                    command=install_cmd,
                    working_dir='/app',
                    volumes={str(repo_path): {'bind': '/app', 'mode': 'rw'}},
                    mem_limit=self.memory_limit,
                    nano_cpus=int(float(self.cpu_limit) * 1_000_000_000),
                        environment={
                            'PYTHONDONTWRITEBYTECODE': '1',
                            'PYTEST_ADDOPTS': '-p no:cacheprovider',
                        },
                    security_opt=['no-new-privileges'],
                    read_only=False,  # Need write access for pip cache
                    detach=True
                )
                
                # Start container
                container.start()
                
                # Wait for completion
                exit_code = container.wait(timeout=self.timeout)
                
                if exit_code['StatusCode'] == 0:
                    result['success'] = True
                    logger.info("Dependencies installed successfully")
                else:
                    logs = container.logs().decode('utf-8')
                    result['errors'].append(f"Installation failed: {logs}")
                    logger.error(f"Dependency installation failed: {logs}")
                
            except Exception as e:
                result['errors'].append(f"Container error: {str(e)}")
            finally:
                if container:
                    try:
                        container.remove(force=True)
                    except Exception as e:
                        logger.warning(f"Error removing container: {e}")
            
            result['dependencies'] = dependencies
            
        except Exception as e:
            result['errors'].append(f"Installation error: {str(e)}")
            logger.error(f"Error installing dependencies: {e}")
        
        return result
    
    async def _run_tests(self, repo_path: Path) -> Dict[str, Any]:
        """Run repository tests"""
        result = {'success': False, 'output': '', 'errors': []}
        
        try:
            # Look for test commands
            test_commands = []
            
            # Check for common test files and commands
            test_indicators = [
                (repo_path / 'pytest.ini', ['python', '-m', 'pytest', '-v']),
                (repo_path / 'tox.ini', ['python', '-m', 'pytest', '-v']),
                (repo_path / 'setup.cfg', ['python', '-m', 'pytest', '-v']),
                (Path(repo_path) / 'tests', ['python', '-m', 'pytest', 'tests/', '-v']),
                (Path(repo_path) / 'test', ['python', '-m', 'pytest', 'test/', '-v']),
            ]
            
            for indicator, cmd in test_indicators:
                if indicator.exists():
                    test_commands.append(cmd)
                    break
            
            # Default test command if no specific configuration found
            if not test_commands:
                # Try to find Python test files
                test_files = list(repo_path.rglob('*test*.py'))
                if test_files:
                    test_commands.append(['python', '-m', 'pytest', '-v'])
                else:
                    # No tests found
                    result['success'] = True  # No tests to run
                    result['output'] = "No tests found in repository"
                    return result
            
            # Run tests in Docker container
            container = None
            try:
                for cmd in test_commands:
                    test_bootstrap = (
                        'python -m pip install --disable-pip-version-check --upgrade pip && '
                        'python -m pip install --disable-pip-version-check pytest && '
                        'if [ -f requirements.txt ]; then python -m pip install -r requirements.txt; '
                        'elif [ -f setup.py ] || [ -f pyproject.toml ]; then python -m pip install -e .; fi && '
                        'if [ -f pyproject.toml ] && grep -q "^\\\\[dependency-groups\\\\]" pyproject.toml '
                        '&& grep -q "^tests = \\\\[" pyproject.toml; then '
                        'python -m pip install --group tests; fi && '
                    )
                    test_command = ['sh', '-lc', test_bootstrap + ' '.join(cmd)]
                    container = self.docker_client.containers.create(
                        image=self.image_name,
                        command=test_command,
                        working_dir='/app',
                        volumes={str(repo_path): {'bind': '/app', 'mode': 'rw'}},
                        mem_limit=self.memory_limit,
                        nano_cpus=int(float(self.cpu_limit) * 1_000_000_000),
                        environment={
                            'PYTHONDONTWRITEBYTECODE': '1',
                            'PYTEST_ADDOPTS': '-p no:cacheprovider',
                        },
                        security_opt=['no-new-privileges'],
                        detach=True
                    )
                    
                    container.start()
                    
                    # Wait for completion
                    exit_code = container.wait(timeout=self.timeout)
                    logs = container.logs().decode('utf-8')
                    
                    if exit_code['StatusCode'] == 0:
                        result['success'] = True
                        result['output'] = logs
                        logger.info("Tests executed successfully")
                        break
                    else:
                        result['errors'].append(f"Test command failed: {cmd}")
                        result['output'] = logs
                    
                    # Clean up container
                    container.remove(force=True)
                    container = None
                
            except Exception as e:
                result['errors'].append(f"Test execution error: {str(e)}")
            finally:
                if container:
                    try:
                        container.remove(force=True)
                    except Exception as e:
                        logger.warning(f"Error removing test container: {e}")
        
        except Exception as e:
            result['errors'].append(f"Test setup error: {str(e)}")
            logger.error(f"Error running tests: {e}")
        
        return result
    
    async def _calculate_setup_complexity_score(self, result: SandboxResult, repo_data: Dict[str, Any]) -> float:
        """Calculate setup complexity score (0-1, where 1 is most complex)"""
        score = 0.0
        
        try:
            # Base complexity from dependencies
            dependency_count = len(result.dependencies)
            if dependency_count > 50:
                score += 0.3
            elif dependency_count > 20:
                score += 0.2
            elif dependency_count > 10:
                score += 0.1
            
            # Installation success
            if not result.install_success:
                score += 0.4
            
            # Test complexity
            if not result.test_success:
                score += 0.2
            
            # File structure complexity
            total_files = result.file_structure.get('total_files', 0)
            if total_files > 1000:
                score += 0.2
            elif total_files > 500:
                score += 0.1
            
            # Security issues increase complexity
            security_issues_count = len(result.security_issues)
            if security_issues_count > 5:
                score += 0.3
            elif security_issues_count > 2:
                score += 0.15
            
            # Language diversity
            language_count = len(result.file_structure.get('languages', {}))
            if language_count > 5:
                score += 0.1
            
            # Configuration files complexity
            config_files = result.file_structure.get('config_files', [])
            if len(config_files) > 3:
                score += 0.1
            
            # Cap at 1.0
            score = min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating setup complexity: {e}")
            score = 0.5  # Default to medium complexity
        
        return score
    
    async def _collect_performance_metrics(self, repo_path: Path) -> Dict[str, Any]:
        """Collect performance metrics from repository"""
        metrics = {
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'max_file_size': 0,
            'average_file_size': 0,
            'test_coverage': 0.0,
            'cyclomatic_complexity': 0
        }
        
        try:
            total_size = 0
            file_count = 0
            
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c']:
                    try:
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        file_count += 1
                        metrics['max_file_size'] = max(metrics['max_file_size'], file_size)
                        
                        # Count lines for Python files
                        if file_path.suffix == '.py':
                            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                content = await f.read()
                                lines = content.split('\n')
                                for line in lines:
                                    if line.strip():
                                        if line.strip().startswith('#'):
                                            metrics['comment_lines'] += 1
                                        else:
                                            metrics['code_lines'] += 1
                                    else:
                                        metrics['blank_lines'] += 1
                    
                    except Exception as e:
                        logger.debug(f"Error analyzing file {file_path}: {e}")
            
            if file_count > 0:
                metrics['average_file_size'] = total_size / file_count
        
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
        
        return metrics
    
    def _is_safe_url(self, url: str) -> bool:
        """Check if URL is safe for cloning"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc in self.allowed_domains
        except Exception:
            return False
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.debug(f"Error calculating directory size: {e}")
        return total_size
    
    async def batch_analyze_repositories(self, repositories: List[Dict[str, Any]]) -> List[SandboxResult]:
        """Analyze multiple repositories in parallel"""
        semaphore = asyncio.Semaphore(3)  # Limit concurrent sandbox executions
        
        async def analyze_with_semaphore(repo_data):
            async with semaphore:
                return await self.analyze_repository_in_sandbox(repo_data)
        
        tasks = [analyze_with_semaphore(repo) for repo in repositories]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing repository {repositories[i].get('name', 'unknown')}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def cleanup(self):
        """Clean up Docker resources"""
        try:
            if self.docker_client:
                # Remove stopped containers
                containers = self.docker_client.containers.list(all=True, filters={'status': 'exited'})
                for container in containers:
                    try:
                        container.remove()
                    except Exception as e:
                        logger.debug(f"Error removing container {container.id}: {e}")
                
                # Clean up unused images
                self.docker_client.images.prune()
        except Exception as e:
            logger.error(f"Error during Docker cleanup: {e}")

# Global sandbox manager instance
sandbox_manager = None

def init_sandbox_manager(config: Dict[str, Any] = None) -> DockerSandboxManager:
    """Initialize global sandbox manager instance"""
    global sandbox_manager
    sandbox_manager = DockerSandboxManager(config or {})
    return sandbox_manager

def get_sandbox_manager() -> DockerSandboxManager:
    """Get global sandbox manager instance"""
    if sandbox_manager is None:
        raise RuntimeError("Sandbox manager not initialized. Call init_sandbox_manager() first.")
    return sandbox_manager
"""GitHub repository parser."""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from github import Github
from parsers.codebase import CodebaseParser


class GitHubParser:
    """Parser for GitHub repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub parser.
        
        Args:
            github_token: Optional GitHub personal access token
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.github_token) if self.github_token else None
    
    def parse_repo(self, repo_url: str, max_files: int = 50) -> str:
        """
        Parse GitHub repository and return codebase summary.
        
        Args:
            repo_url: GitHub repository URL (e.g., "owner/repo" or full URL)
            max_files: Maximum number of files to analyze
            
        Returns:
            Formatted codebase structure summary
        """
        # Extract owner/repo from URL
        repo_name = self._extract_repo_name(repo_url)
        
        if not self.github:
            return f"Error: GitHub token not configured. Set GITHUB_TOKEN environment variable."
        
        try:
            # Get repository
            repo = self.github.get_repo(repo_name)
            
            # Clone to temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_path = Path(tmpdir) / repo.name
                
                # Clone repository
                import subprocess
                clone_url = repo.clone_url
                if self.github_token:
                    # Use token in URL for private repos
                    clone_url = clone_url.replace("https://", f"https://{self.github_token}@")
                
                subprocess.run(
                    ["git", "clone", "--depth", "1", clone_url, str(clone_path)],
                    check=True,
                    capture_output=True
                )
                
                # Analyze using CodebaseParser
                parser = CodebaseParser(str(clone_path))
                summary = parser.analyze(max_files)
                
                # Add repo metadata
                metadata = f"Repository: {repo.full_name}\nDescription: {repo.description or 'N/A'}\nLanguage: {repo.language or 'N/A'}\n\n"
                return metadata + summary
        
        except Exception as e:
            return f"Error parsing repository: {str(e)}"
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """
        Extract owner/repo from various URL formats.
        
        Args:
            repo_url: Repository URL or "owner/repo" format
            
        Returns:
            "owner/repo" string
        """
        # If already in owner/repo format
        if '/' in repo_url and repo_url.count('/') == 1 and not repo_url.startswith('http'):
            return repo_url
        
        # Extract from URL
        if 'github.com' in repo_url:
            parts = repo_url.replace('https://', '').replace('http://', '').split('/')
            if len(parts) >= 3:
                return f"{parts[1]}/{parts[2].replace('.git', '')}"
        
        return repo_url


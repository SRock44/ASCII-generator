"""Codebase parser for analyzing local code structure."""
import os
from pathlib import Path
from typing import Dict, List, Set


class CodebaseParser:
    """Parser for analyzing local codebase structure."""
    
    # Common file extensions to analyze
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.cs',
        '.html', '.css', '.vue', '.svelte'
    }
    
    # Directories to ignore
    IGNORE_DIRS = {
        '__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env',
        'dist', 'build', '.cache', '.pytest_cache', '.mypy_cache',
        'target', 'bin', 'obj', '.idea', '.vscode'
    }
    
    def __init__(self, root_path: str = "."):
        """
        Initialize codebase parser.
        
        Args:
            root_path: Root directory to analyze
        """
        self.root_path = Path(root_path).resolve()
    
    def analyze(self, max_files: int = 50) -> str:
        """
        Analyze codebase structure and return summary.
        
        Args:
            max_files: Maximum number of files to analyze
            
        Returns:
            Formatted codebase structure summary
        """
        structure = self._get_structure(max_files)
        imports = self._get_imports(structure)
        summary = self._format_summary(structure, imports)
        return summary
    
    def _get_structure(self, max_files: int) -> Dict[str, List[str]]:
        """
        Get codebase file structure.
        
        Args:
            max_files: Maximum files to process
            
        Returns:
            Dictionary mapping directories to file lists
        """
        structure = {}
        file_count = 0
        
        for root, dirs, files in os.walk(self.root_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            # Get relative path
            rel_root = os.path.relpath(root, self.root_path)
            if rel_root == '.':
                rel_root = ''
            
            # Collect code files
            code_files = []
            for file in files:
                if file_count >= max_files:
                    break
                
                ext = Path(file).suffix.lower()
                if ext in self.CODE_EXTENSIONS:
                    code_files.append(file)
                    file_count += 1
            
            if code_files:
                structure[rel_root or '.'] = sorted(code_files)
            
            if file_count >= max_files:
                break
        
        return structure
    
    def _get_imports(self, structure: Dict[str, List[str]]) -> Dict[str, Set[str]]:
        """
        Extract import statements from files.
        
        Args:
            structure: File structure dictionary
            
        Returns:
            Dictionary mapping files to their imports
        """
        imports = {}
        
        for dir_path, files in structure.items():
            full_dir = self.root_path / dir_path if dir_path != '.' else self.root_path
            
            for file in files[:10]:  # Limit to first 10 files per directory
                file_path = full_dir / file
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        file_imports = self._extract_imports(content, file_path.suffix)
                        if file_imports:
                            rel_file = f"{dir_path}/{file}" if dir_path != '.' else file
                            imports[rel_file] = file_imports
                except Exception:
                    continue
        
        return imports
    
    def _extract_imports(self, content: str, ext: str) -> Set[str]:
        """
        Extract import statements based on file extension.
        
        Args:
            content: File content
            ext: File extension
            
        Returns:
            Set of imported modules
        """
        imports = set()
        lines = content.split('\n')
        
        for line in lines[:100]:  # Check first 100 lines
            line = line.strip()
            
            if ext == '.py':
                if line.startswith('import ') or line.startswith('from '):
                    # Extract module name
                    if line.startswith('import '):
                        module = line[7:].split()[0].split('.')[0]
                    else:  # from ... import
                        parts = line.split()
                        if len(parts) >= 2:
                            module = parts[1].split('.')[0]
                    imports.add(module)
            
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                if line.startswith('import ') or line.startswith('require('):
                    # Extract module name
                    if 'from' in line:
                        module = line.split('from')[1].strip().split()[0].strip("'\"")
                    elif 'require(' in line:
                        module = line.split('require(')[1].split(')')[0].strip("'\"")
                    imports.add(module)
        
        return imports
    
    def _format_summary(self, structure: Dict[str, List[str]], imports: Dict[str, Set[str]]) -> str:
        """
        Format codebase summary for AI analysis.
        
        Args:
            structure: File structure
            imports: Import relationships
            
        Returns:
            Formatted summary string
        """
        summary_parts = ["Codebase Structure:\n"]
        
        # Add directory structure
        for dir_path, files in sorted(structure.items()):
            summary_parts.append(f"\nDirectory: {dir_path or '.'}")
            for file in files[:5]:  # Limit files per directory
                summary_parts.append(f"  - {file}")
            if len(files) > 5:
                summary_parts.append(f"  ... and {len(files) - 5} more files")
        
        # Add import relationships
        if imports:
            summary_parts.append("\n\nKey Dependencies:")
            for file, file_imports in list(imports.items())[:20]:
                if file_imports:
                    summary_parts.append(f"\n{file}:")
                    summary_parts.append(f"  imports: {', '.join(sorted(list(file_imports)[:5]))}")
        
        return "\n".join(summary_parts)







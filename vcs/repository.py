import os
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


class Repository:
    """Core repository class that handles all VCS operations."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.vcs_dir = self.root_path / ".vcs"
        self.objects_dir = self.vcs_dir / "objects"
        self.refs_dir = self.vcs_dir / "refs"
        self.staging_file = self.vcs_dir / "staging.json"
        self.head_file = self.vcs_dir / "HEAD"
        self.config_file = self.vcs_dir / "config.json"
        
    def init(self) -> bool:
        """Initialize a new repository."""
        if self.vcs_dir.exists():
            return False
            
        # Create directory structure
        self.vcs_dir.mkdir()
        self.objects_dir.mkdir()
        self.refs_dir.mkdir()
        (self.refs_dir / "heads").mkdir()
        
        # Initialize empty staging area
        self._write_json(self.staging_file, {})
        
        # Set initial branch to main
        self._write_file(self.head_file, "ref: refs/heads/main")
        
        # Initialize config
        config = {
            "repository_version": "1",
            "created_at": datetime.now().isoformat()
        }
        self._write_json(self.config_file, config)
        
        return True
    
    def is_repository(self) -> bool:
        """Check if current directory is a VCS repository."""
        return self.vcs_dir.exists() and self.vcs_dir.is_dir()
    
    def add(self, file_paths: List[str]) -> Dict[str, str]:
        """Add files to staging area."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        staging = self._read_json(self.staging_file, {})
        results = {}
        
        for file_path in file_paths:
            full_path = self.root_path / file_path
            if not full_path.exists():
                results[file_path] = "error: file not found"
                continue
                
            if full_path.is_dir():
                results[file_path] = "error: is a directory"
                continue
                
            # Calculate file hash
            content = self._read_file(full_path)
            file_hash = self._hash_content(content)
            
            # Store file object
            self._store_object(file_hash, content)
            
            # Add to staging
            staging[file_path] = {
                "hash": file_hash,
                "mode": "100644",  # Regular file
                "staged_at": datetime.now().isoformat()
            }
            results[file_path] = "added"
            
        self._write_json(self.staging_file, staging)
        return results
    
    def commit(self, message: str, author: str = "Unknown") -> str:
        """Create a new commit from staged files."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        staging = self._read_json(self.staging_file, {})
        if not staging:
            raise Exception("No changes staged for commit")
            
        # Get parent commit
        parent_hash = self._get_current_commit()
        
        # Create commit object
        commit = {
            "message": message,
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "parent": parent_hash,
            "tree": staging.copy()
        }
        
        # Generate commit hash and store
        commit_content = json.dumps(commit, sort_keys=True)
        commit_hash = self._hash_content(commit_content)
        self._store_object(commit_hash, commit_content)
        
        # Update branch reference
        current_branch = self._get_current_branch()
        branch_file = self.refs_dir / "heads" / current_branch
        self._write_file(branch_file, commit_hash)
        
        # Clear staging area
        self._write_json(self.staging_file, {})
        
        return commit_hash
    
    def status(self) -> Dict[str, any]:
        """Get repository status."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        staging = self._read_json(self.staging_file, {})
        current_commit_hash = self._get_current_commit()
        current_branch = self._get_current_branch()
        
        # Get committed files from current commit
        committed_files = {}
        if current_commit_hash:
            commit = self._get_commit(current_commit_hash)
            committed_files = commit.get("tree", {})
        
        # Find modified files
        modified = []
        for file_path in committed_files:
            full_path = self.root_path / file_path
            if not full_path.exists():
                modified.append(f"{file_path} (deleted)")
                continue
                
            current_content = self._read_file(full_path)
            current_hash = self._hash_content(current_content)
            
            if current_hash != committed_files[file_path]["hash"]:
                modified.append(file_path)
        
        # Find untracked files
        untracked = []
        for file_path in self._get_all_files():
            if file_path not in committed_files and file_path not in staging:
                untracked.append(file_path)
        
        return {
            "branch": current_branch,
            "staged": list(staging.keys()),
            "modified": modified,
            "untracked": untracked
        }
    
    def log(self, limit: int = 10) -> List[Dict]:
        """Get commit history."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        commits = []
        current_hash = self._get_current_commit()
        
        while current_hash and len(commits) < limit:
            commit = self._get_commit(current_hash)
            if not commit:
                break
                
            commits.append({
                "hash": current_hash,
                "message": commit["message"],
                "author": commit["author"],
                "timestamp": commit["timestamp"]
            })
            
            current_hash = commit.get("parent")
            
        return commits
    
    def branch(self, branch_name: str = None) -> any:
        """Create a new branch or list branches."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        if branch_name is None:
            # List branches
            branches = []
            current_branch = self._get_current_branch()
            heads_dir = self.refs_dir / "heads"
            
            if heads_dir.exists():
                for branch_file in heads_dir.iterdir():
                    if branch_file.is_file():
                        name = branch_file.name
                        is_current = name == current_branch
                        branches.append({"name": name, "current": is_current})
            
            return branches
        else:
            # Create new branch
            current_commit = self._get_current_commit()
            if not current_commit:
                raise Exception("No commits yet, cannot create branch")
                
            branch_file = self.refs_dir / "heads" / branch_name
            if branch_file.exists():
                raise Exception(f"Branch '{branch_name}' already exists")
                
            self._write_file(branch_file, current_commit)
            return f"Branch '{branch_name}' created"
    
    def checkout(self, branch_name: str) -> str:
        """Switch to a different branch."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        branch_file = self.refs_dir / "heads" / branch_name
        if not branch_file.exists():
            raise Exception(f"Branch '{branch_name}' does not exist")
            
        # Update HEAD to point to new branch
        self._write_file(self.head_file, f"ref: refs/heads/{branch_name}")
        
        # Update working directory to match branch state
        commit_hash = self._read_file(branch_file).strip()
        if commit_hash:
            self._checkout_commit(commit_hash)
            
        return f"Switched to branch '{branch_name}'"
    
    def merge(self, branch_name: str) -> str:
        """Merge another branch into current branch."""
        if not self.is_repository():
            raise Exception("Not a VCS repository")
            
        current_branch = self._get_current_branch()
        if branch_name == current_branch:
            raise Exception("Cannot merge branch into itself")
            
        branch_file = self.refs_dir / "heads" / branch_name
        if not branch_file.exists():
            raise Exception(f"Branch '{branch_name}' does not exist")
            
        # Get commit hashes
        current_commit_hash = self._get_current_commit()
        merge_commit_hash = self._read_file(branch_file).strip()
        
        if not current_commit_hash:
            # Fast-forward merge (no commits on current branch)
            current_branch_file = self.refs_dir / "heads" / current_branch
            self._write_file(current_branch_file, merge_commit_hash)
            self._checkout_commit(merge_commit_hash)
            return f"Fast-forward merge of '{branch_name}'"
        
        # Simple merge strategy: take files from merge branch
        merge_commit = self._get_commit(merge_commit_hash)
        current_commit = self._get_commit(current_commit_hash)
        
        # Combine trees (merge branch takes precedence)
        merged_tree = current_commit.get("tree", {}).copy()
        merged_tree.update(merge_commit.get("tree", {}))
        
        # Create merge commit
        commit = {
            "message": f"Merge branch '{branch_name}'",
            "author": "System",
            "timestamp": datetime.now().isoformat(),
            "parent": current_commit_hash,
            "merge_parent": merge_commit_hash,
            "tree": merged_tree
        }
        
        commit_content = json.dumps(commit, sort_keys=True)
        new_commit_hash = self._hash_content(commit_content)
        self._store_object(new_commit_hash, commit_content)
        
        # Update current branch
        current_branch_file = self.refs_dir / "heads" / current_branch
        self._write_file(current_branch_file, new_commit_hash)
        
        # Update working directory
        self._checkout_commit(new_commit_hash)
        
        return f"Merged branch '{branch_name}'"
    
    # Helper methods
    def _hash_content(self, content: str) -> str:
        """Generate SHA-1 hash of content."""
        return hashlib.sha1(content.encode()).hexdigest()
    
    def _store_object(self, hash_value: str, content: str):
        """Store object in objects directory."""
        obj_dir = self.objects_dir / hash_value[:2]
        obj_dir.mkdir(exist_ok=True)
        obj_file = obj_dir / hash_value[2:]
        self._write_file(obj_file, content)
    
    def _get_object(self, hash_value: str) -> Optional[str]:
        """Retrieve object from objects directory."""
        obj_file = self.objects_dir / hash_value[:2] / hash_value[2:]
        if obj_file.exists():
            return self._read_file(obj_file)
        return None
    
    def _get_current_branch(self) -> str:
        """Get current branch name."""
        head_content = self._read_file(self.head_file).strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]  # Remove "ref: refs/heads/"
        return "main"  # Default branch
    
    def _get_current_commit(self) -> Optional[str]:
        """Get current commit hash."""
        current_branch = self._get_current_branch()
        branch_file = self.refs_dir / "heads" / current_branch
        if branch_file.exists():
            return self._read_file(branch_file).strip()
        return None
    
    def _get_commit(self, commit_hash: str) -> Optional[Dict]:
        """Get commit object by hash."""
        content = self._get_object(commit_hash)
        if content:
            return json.loads(content)
        return None
    
    def _checkout_commit(self, commit_hash: str):
        """Update working directory to match commit state."""
        commit = self._get_commit(commit_hash)
        if not commit:
            return
            
        tree = commit.get("tree", {})
        
        # Remove files not in commit
        for file_path in self._get_all_files():
            if file_path not in tree:
                full_path = self.root_path / file_path
                if full_path.exists():
                    full_path.unlink()
        
        # Restore files from commit
        for file_path, file_info in tree.items():
            content = self._get_object(file_info["hash"])
            if content:
                full_path = self.root_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                self._write_file(full_path, content)
    
    def _get_all_files(self) -> Set[str]:
        """Get all files in working directory (excluding .vcs)."""
        files = set()
        for item in self.root_path.rglob("*"):
            if item.is_file() and not str(item).startswith(str(self.vcs_dir)):
                rel_path = item.relative_to(self.root_path)
                files.add(str(rel_path))
        return files
    
    def _read_file(self, file_path: Path) -> str:
        """Read file content."""
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return file_path.read_text(encoding='latin-1')
    
    def _write_file(self, file_path: Path, content: str):
        """Write content to file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
    
    def _read_json(self, file_path: Path, default=None):
        """Read JSON file."""
        if not file_path.exists():
            return default
        try:
            return json.loads(file_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return default
    
    def _write_json(self, file_path: Path, data):
        """Write data to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(data, indent=2))
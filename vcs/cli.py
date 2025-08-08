#!/usr/bin/env python3
"""
CLI interface for the Python Version Control System.
Provides a git-like command-line interface for version control operations.
"""

import sys
import argparse
from pathlib import Path
from typing import List

from .repository import Repository


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class VCSCli:
    """Command-line interface for VCS operations."""
    
    def __init__(self):
        self.repo = Repository()
        
    def colorize(self, text: str, color: str) -> str:
        """Add color to text if stdout is a TTY."""
        if sys.stdout.isatty():
            return f"{color}{text}{Colors.ENDC}"
        return text
    
    def print_success(self, message: str):
        """Print success message."""
        print(self.colorize(message, Colors.OKGREEN))
    
    def print_error(self, message: str):
        """Print error message."""
        print(self.colorize(f"Error: {message}", Colors.FAIL), file=sys.stderr)
    
    def print_warning(self, message: str):
        """Print warning message."""
        print(self.colorize(f"Warning: {message}", Colors.WARNING))
    
    def print_info(self, message: str):
        """Print info message."""
        print(self.colorize(message, Colors.OKBLUE))
    
    def cmd_init(self, args):
        """Initialize a new repository."""
        try:
            if self.repo.init():
                self.print_success("Initialized empty VCS repository")
            else:
                self.print_error("Repository already exists")
                return 1
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_add(self, args):
        """Add files to staging area."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
            
        if not args.files:
            self.print_error("No files specified")
            return 1
        
        try:
            results = self.repo.add(args.files)
            for file_path, status in results.items():
                if status == "added":
                    self.print_success(f"Added: {file_path}")
                else:
                    self.print_error(f"{file_path}: {status}")
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_commit(self, args):
        """Create a new commit."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
            
        if not args.message:
            self.print_error("Commit message required")
            return 1
        
        try:
            commit_hash = self.repo.commit(args.message, args.author or "Unknown")
            self.print_success(f"Committed: {commit_hash[:8]}")
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_status(self, args):
        """Show repository status."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
        
        try:
            status = self.repo.status()
            
            # Print current branch
            print(f"On branch {self.colorize(status['branch'], Colors.BOLD)}")
            print()
            
            # Print staged files
            if status['staged']:
                print(self.colorize("Changes to be committed:", Colors.OKGREEN))
                for file_path in status['staged']:
                    print(f"  {self.colorize('new file:', Colors.OKGREEN)}   {file_path}")
                print()
            
            # Print modified files
            if status['modified']:
                print(self.colorize("Changes not staged for commit:", Colors.FAIL))
                for file_path in status['modified']:
                    print(f"  {self.colorize('modified:', Colors.FAIL)}    {file_path}")
                print()
            
            # Print untracked files
            if status['untracked']:
                print(self.colorize("Untracked files:", Colors.WARNING))
                for file_path in status['untracked']:
                    print(f"  {file_path}")
                print()
                
            if not any([status['staged'], status['modified'], status['untracked']]):
                self.print_info("Nothing to commit, working tree clean")
                
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_log(self, args):
        """Show commit history."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
        
        try:
            commits = self.repo.log(args.limit)
            if not commits:
                self.print_info("No commits yet")
                return 0
                
            for commit in commits:
                print(self.colorize(f"commit {commit['hash']}", Colors.WARNING))
                print(f"Author: {commit['author']}")
                print(f"Date: {commit['timestamp']}")
                print()
                # Indent commit message
                for line in commit['message'].split('\n'):
                    print(f"    {line}")
                print()
                
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_branch(self, args):
        """Create or list branches."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
        
        try:
            if args.name:
                # Create branch
                result = self.repo.branch(args.name)
                self.print_success(result)
            else:
                # List branches
                branches = self.repo.branch()
                if not branches:
                    self.print_info("No branches found")
                    return 0
                    
                for branch in branches:
                    if branch['current']:
                        print(self.colorize(f"* {branch['name']}", Colors.OKGREEN))
                    else:
                        print(f"  {branch['name']}")
                        
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_checkout(self, args):
        """Switch branches."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
            
        if not args.branch:
            self.print_error("Branch name required")
            return 1
        
        try:
            result = self.repo.checkout(args.branch)
            self.print_success(result)
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0
    
    def cmd_merge(self, args):
        """Merge branches."""
        if not self.repo.is_repository():
            self.print_error("Not a VCS repository")
            return 1
            
        if not args.branch:
            self.print_error("Branch name required")
            return 1
        
        try:
            result = self.repo.merge(args.branch)
            self.print_success(result)
        except Exception as e:
            self.print_error(str(e))
            return 1
        return 0


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog='vcs',
        description='A minimal version control system',
        epilog='Use "vcs <command> --help" for more information on a specific command.'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new repository')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add files to staging area')
    add_parser.add_argument('files', nargs='+', help='Files to add')
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Create a new commit')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')
    commit_parser.add_argument('-a', '--author', help='Commit author')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show repository status')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Show commit history')
    log_parser.add_argument('-n', '--limit', type=int, default=10, help='Limit number of commits')
    
    # Branch command
    branch_parser = subparsers.add_parser('branch', help='Create or list branches')
    branch_parser.add_argument('name', nargs='?', help='Branch name to create')
    
    # Checkout command
    checkout_parser = subparsers.add_parser('checkout', help='Switch branches')
    checkout_parser.add_argument('branch', help='Branch name to switch to')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge branches')
    merge_parser.add_argument('branch', help='Branch name to merge')
    
    return parser


def main(argv: List[str] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = VCSCli()
    
    # Route to appropriate command handler
    command_handlers = {
        'init': cli.cmd_init,
        'add': cli.cmd_add,
        'commit': cli.cmd_commit,
        'status': cli.cmd_status,
        'log': cli.cmd_log,
        'branch': cli.cmd_branch,
        'checkout': cli.cmd_checkout,
        'merge': cli.cmd_merge,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
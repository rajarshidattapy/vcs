#!/usr/bin/env python3
"""
VCS - A minimal Python version control system
Main entry point for the CLI application.
"""

import sys
from vcs.cli import main

if __name__ == '__main__':
    sys.exit(main())
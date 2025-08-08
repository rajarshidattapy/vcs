# VCS

A minimal version control system implemented in Python that captures Git's core MVP functionality. This demonstrates how Git's essential features can be implemented with a clean, simple architecture.

## 🎯 What's Implemented (MVP Features)

### ✅ Core Repository Operations
- **Repository initialization** (`vcs init`)
- **File staging area** (`vcs add <files>`)
- **Commit creation** (`vcs commit -m "message"`)
- **Repository status** (`vcs status`)
- **Commit history** (`vcs log`)

### ✅ Branching & Merging
- **Branch creation** (`vcs branch <name>`)
- **Branch listing** (`vcs branch`)
- **Branch switching** (`vcs checkout <branch>`)
- **Simple merging** (`vcs merge <branch>`)

### ✅ Storage & Integrity
- **Object storage** (SHA-1 hashing)
- **File content tracking**
- **Commit metadata** (author, timestamp, message)
- **Branch references**

### ✅ User Interface
- **CLI with colored output**
- **Error handling and validation**
- **Git-like command structure**

## 🚧 What's Missing (Full Git Features)

### Remote Operations
- [ ] Remote repositories (`git remote`, `git push`, `git pull`)
- [ ] Clone functionality (`git clone`)
- [ ] Fetch operations (`git fetch`)

### Advanced Branching
- [ ] Merge conflict resolution
- [ ] Rebase operations (`git rebase`)
- [ ] Cherry-picking (`git cherry-pick`)
- [ ] Branch deletion (`git branch -d`)

### File Operations
- [ ] File removal tracking (`git rm`)
- [ ] File moving/renaming (`git mv`)
- [ ] Ignore patterns (`.gitignore`)
- [ ] File permissions tracking

### History & Navigation
- [ ] Commit diffs (`git diff`)
- [ ] Blame/annotate (`git blame`)
- [ ] Reset operations (`git reset`)
- [ ] Checkout specific commits
- [ ] Tags (`git tag`)

### Advanced Features
- [ ] Stashing (`git stash`)
- [ ] Submodules (`git submodule`)
- [ ] Hooks (pre-commit, post-commit, etc.)
- [ ] Worktrees (`git worktree`)
- [ ] Bisect (`git bisect`)

### Performance & Storage
- [ ] Object compression
- [ ] Pack files
- [ ] Garbage collection
- [ ] Large file handling (LFS)

### Configuration
- [ ] Global/local config (`git config`)
- [ ] User identity management
- [ ] Aliases
- [ ] Core settings

## 📋 Usage

### Basic Workflow
```bash
# Initialize repository
python vcs.py init

# Add files to staging
python vcs.py add file1.txt file2.py

# Create commit
python vcs.py commit -m "Initial commit" -a "Your Name"

# Check status
python vcs.py status

# View history
python vcs.py log
```

### Branching Workflow
```bash
# Create and switch to new branch
python vcs.py branch feature-branch
python vcs.py checkout feature-branch

# Make changes and commit
python vcs.py add modified-file.txt
python vcs.py commit -m "Add new feature"

# Switch back and merge
python vcs.py checkout main
python vcs.py merge feature-branch
```

## 🏗️ Architecture

```
.vcs/
├── objects/          # Content-addressable storage
│   └── ab/cdef123... # SHA-1 hashed objects
├── refs/heads/       # Branch references
├── HEAD              # Current branch pointer
├── config.json       # Repository metadata
└── staging.json      # Staged files index
```


## 🚀 MVP Philosophy

This VCS proves that Git's core value can be delivered with minimal features:
- **Local version control** without network dependencies
- **Reliable change tracking** with cryptographic integrity
- **Branching and merging** for parallel development
- **Simple CLI** for developer workflow

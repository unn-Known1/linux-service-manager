#!/bin/bash
#
# Setup GitHub repository for Linux Service Manager
# Usage: GITHUB_TOKEN=your_token ./setup-github-repo.sh
#
# SECURITY: Never commit this token or echo it to logs

set -e
set -u

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check for token
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo_error "GITHUB_TOKEN environment variable not set"
    echo "Usage: GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx ./setup-github-repo.sh"
    exit 1
fi

# Verify token format (basic check)
if ! [[ "$GITHUB_TOKEN" =~ ^ghp_ ]]; then
    echo_warn "Token doesn't start with 'ghp_' - make sure it's a GitHub token"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REPO_NAME="linux-service-manager"
REPO_DESCRIPTION="A practical Linux service manager demonstrating system calls, daemonization, process management, and shell integration. Educational tool for understanding Unix daemon patterns."
REPO_HOMEPAGE="https://github.com/$(git config user.name 2>/dev/null || echo 'username')/$REPO_NAME"

echo_info "Setting up GitHub repository: $REPO_NAME"
echo ""

# Create repository using GitHub API
echo_info "Creating repository on GitHub..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/user/repos" \
    -d "{\"name\":\"$REPO_NAME\",\"description\":\"$REPO_DESCRIPTION\",\"homepage\":\"$REPO_HOMEPAGE\",\"public\":true,\"auto_init\":false}")

HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" -ne 201 ]; then
    echo_error "Failed to create repository (HTTP $HTTP_CODE)"
    echo "Response: $HTTP_BODY"
    # Check if repository already exists
    if echo "$HTTP_BODY" | grep -q "already exists"; then
        echo_warn "Repository may already exist. Will try to use it."
    else
        exit 1
    fi
else
    echo_info "Repository created successfully!"
    REPO_URL=$(echo "$HTTP_BODY" | grep -o '"clone_url":"[^"]*"' | cut -d'"' -f4)
    echo "  URL: $REPO_URL"
fi

# Use repository URL if extracted, otherwise construct
: "${REPO_URL:=https://github.com/$(git config user.name 2>/dev/null || echo 'username')/$REPO_NAME.git}"

echo ""
echo_info "Configuring git remote..."

# Remove any existing remote named 'github'
git remote remove github 2>/dev/null || true

# Add remote with token authentication (using token as password)
git remote add github "$REPO_URL"

# Configure credential helper for this remote to use token
# We'll push using the token directly in the URL, but first let's verify local repo state
echo_info "Checking repository contents..."
git status

# Create .gitignore if not exists
if [ ! -f .gitignore ]; then
    echo_info "Creating .gitignore..."
    cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Service Manager specific
*.pid
services.json
.local/
EOF
    git add .gitignore
fi

# Add all files (excluding ignored)
echo_info "Staging files..."
git add -A

# Check what's staged
STAGED=$(git diff --cached --name-only)
if [ -z "$STAGED" ]; then
    echo_warn "No files staged. Checking if everything is already committed..."
else
    echo "Files to be committed:"
    echo "$STAGED" | sed 's/^/  /'
fi

# Create initial commit if needed
if ! git rev-parse HEAD >/dev/null 2>&1; then
    echo_info "Creating initial commit..."
    git commit -m "Initial commit: Linux Service Manager

- Complete Python utility for managing Linux services
- Demonstrates system calls, daemonization, process management
- Includes comprehensive documentation and tests
- Ready for production use with proper error handling"
else
    echo_info "Repository already has commits, will push latest"
fi

# Push to GitHub using token
echo ""
echo_info "Pushing to GitHub..."

# We need to embed the token in the remote URL temporarily
# Extract URL parts
PROTOCOL="${REPO_URL%%://*}"
REST="${REPO_URL#*://}"
if [ "$PROTOCOL" = "https" ]; then
    AUTHED_URL="https://${GITHUB_TOKEN}@${REST}"
else
    echo_error "Only HTTPS URLs supported"
    exit 1
fi

# Push using authenticated URL
if git push "$AUTHED_URL" HEAD:main 2>/dev/null; then
    echo_info "Pushed successfully to main branch"
elif git push "$AUTHED_URL" HEAD:master 2>/dev/null; then
    echo_info "Pushed successfully to master branch"
else
    echo_error "Failed to push. Trying with verbose output..."
    git push "$AUTHED_URL" HEAD:main || git push "$AUTHED_URL" HEAD:master
fi

# Create GitHub release if tag doesn't exist
echo ""
echo_info "Creating GitHub release v1.0.0..."
RELEASE_DATA="{\"tag_name\":\"v1.0.0\",\"target_commitish\":\"main\",\"name\":\"v1.0.0\",\"body\":\"Initial release of Linux Service Manager

## Features
- Full daemonization with double-fork pattern
- Direct Linux system calls via ctypes
- PID management and signal handling
- Privilege dropping (setuid)
- systemd integration
- Comprehensive documentation and tests

## Installation
\`\`\`bash
sudo cp linux-service-manager.py /usr/local/bin/service-manager
sudo chmod +x /usr/local/bin/service-manager
\`\`\`

## Quick Start
\`\`\`bash
service-manager start --name myapp --cmd 'python3 -m http.server 8080'
service-manager status --name myapp
service-manager stop --name myapp
\`\`\`

Full documentation in README.md and QUICKSTART.md.\",\"draft\":false,\"prerelease\":false}"

# Try to create release (may fail if tag exists, that's ok)
curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$(echo "$REST" | cut -d/ -f1-2)/releases" \
    -d "$RELEASE_DATA" > /dev/null 2>&1 && \
    echo_info "GitHub release v1.0.0 created" || \
    echo_warn "Release may already exist or create failed (continuing)"

echo ""
echo "=========================================="
echo_info "Repository setup complete!"
echo "=========================================="
echo ""
echo "Repository URL: https://github.com/$(echo "$REST" | cut -d/ -f1-2)"
echo ""
echo "Next steps:"
echo "1. Visit the repository and verify files are present"
echo "2. Check that README renders correctly"
echo "3. Test cloning: git clone https://github.com/$(echo "$REST" | cut -d/ -f1-2)"
echo ""
echo "To push future updates:"
echo "  git push github HEAD:main"
echo ""
echo "SECURITY REMINDER:"
echo "  - Token was used in this script but not saved"
echo "  - Consider revoking token after setup if not needed"
echo "  - Never commit the token to any file"
echo ""

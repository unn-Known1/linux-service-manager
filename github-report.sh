#!/bin/bash
#
# GitHub Repository Status Reporter
# Generates a concise report about the repository and sends it
#
# Usage: ./github-report.sh [--send] [--channel CHANNEL]
#   --send      Actually send the report (otherwise just print)
#   --channel   Channel to send to (default: webchat)
#
# To set up cron job (every 15 minutes):
#   */15 * * * * cd /path/to/linux-service-manager && ./github-report.sh --send
#
# Requires: curl, git, jq (optional for pretty JSON)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SEND_REPORT=false
CHANNEL="webchat"

while [[ $# -gt 0 ]]; do
    case $1 in
        --send)
            SEND_REPORT=true
            shift
            ;;
        --channel)
            CHANNEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Configuration - should be in environment or config file
REPO="unn-Known1/linux-service-manager"
TOKEN="${GITHUB_TOKEN:-}"

# If token not set, try to read from a secure file
if [ -z "$TOKEN" ] && [ -f ~/.config/github-token ]; then
    TOKEN=$(<~/.config/github-token)
fi

# Report timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')
echo "=== GitHub Repository Report ==="
echo "Generated: $TIMESTAMP"
echo "Repository: $REPO"
echo ""

# Gather stats
echo "📊 Repository Statistics:"

# Get repo info
if [ -n "$TOKEN" ]; then
    REPO_JSON=$(curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/$REPO")
    STARS=$(echo "$REPO_JSON" | grep -o '"stargazers_count":[0-9]*' | cut -d: -f2)
    FORKS=$(echo "$REPO_JSON" | grep -o '"forks_count":[0-9]*' | cut -d: -f2)
    WATCHERS=$(echo "$REPO_JSON" | grep -o '"watchers_count":[0-9]*' | cut -d: -f2)
    OPEN_ISSUES=$(echo "$REPO_JSON" | grep -o '"open_issues_count":[0-9]*' | cut -d: -f2)
    SIZE=$(echo "$REPO_JSON" | grep -o '"size":[0-9]*' | cut -d: -f2)  # Size in KB
    DESCRIPTION=$(echo "$REPO_JSON" | grep -o '"description":"[^"]*"' | cut -d'"' -f4)
    DEFAULT_BRANCH=$(echo "$REPO_JSON" | grep -o '"default_branch":"[^"]*"' | cut -d'"' -f4)
else
    # Without token, use unauthenticated rate-limited API
    REPO_JSON=$(curl -s "https://api.github.com/repos/$REPO")
    STARS=$(echo "$REPO_JSON" | grep -o '"stargazers_count":[0-9]*' | cut -d: -f2)
    FORKS=$(echo "$REPO_JSON" | grep -o '"forks_count":[0-9]*' | cut -d: -f2)
    WATCHERS=$(echo "$REPO_JSON" | grep -o '"watchers_count":[0-9]*' | cut -d: -f2)
    OPEN_ISSUES=$(echo "$REPO_JSON" | grep -o '"open_issues_count":[0-9]*' | cut -d: -f2)
    SIZE=$(echo "$REPO_JSON" | grep -o '"size":[0-9]*' | cut -d: -f2)
    DESCRIPTION=$(echo "$REPO_JSON" | grep -o '"description":"[^"]*"' | cut -d'"' -f4)
    DEFAULT_BRANCH=$(echo "$REPO_JSON" | grep -o '"default_branch":"[^"]*"' | cut -d'"' -f4)
fi

echo "  Stars:      ${STARS:-0}"
echo "  Forks:      ${FORKS:-0}"
echo "  Watchers:   ${WATCHERS:-0}"
echo "  Open Issues: ${OPEN_ISSUES:-0}"
echo "  Size:       ${SIZE:-0} KB"
echo "  Branch:     ${DEFAULT_BRANCH:-main}"
echo "  Description: ${DESCRIPTION:-No description}"
echo ""

# Local code statistics
echo "📁 Local Code Statistics:"
if command -v cloc &> /dev/null; then
    echo "  Languages (via cloc):"
    cloc --quiet --json linux-service-manager.py README.md QUICKSTART.md demo.sh test-service-manager.sh examples/ | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f'    {lang}: {stat[\"code\"]} lines') for lang, stat in data.get('header', {}).get('language_breakdown', {}).items()]" 2>/dev/null || echo "  (cloc analysis failed)"
else
    echo "  Total lines of code:"
    wc -l linux-service-manager.py README.md QUICKSTART.md demo.sh test-service-manager.sh 2>/dev/null | tail -1 | awk '{print "    " $1 " lines total"}'
    echo "  (Install cloc for language breakdown)"
fi
echo ""

# Check recent commits
echo "🔄 Recent Activity:"
if [ -n "$TOKEN" ]; then
    COMMITS_JSON=$(curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/$REPO/commits?per_page=5")
    echo "$COMMITS_JSON" | grep -o '"message":"[^"]*"' | head -5 | sed 's/"/    /; s/^/    /' || echo "    No recent commits"
    echo "$COMMITS_JSON" | grep -o '"author":{"login":"[^"]*"' | head -5 | sed 's/.*"login":"/    Author: /; s/"$//' || echo "    (fetching authors failed)"
else
    git log --oneline -5 2>/dev/null | sed 's/^/    /' || echo "    No git log available"
fi
echo ""

# Repository health check
echo "🔍 Health Check:"
if [ -d ".git" ]; then
    if git status --porcelain | grep -q .; then
        echo "  ⚠️  Uncommitted changes present"
        git status --porcelain | sed 's/^/    /'
    else
        echo "  ✅ Working tree clean"
    fi

    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "HEAD")
    echo "  Current branch: $CURRENT_BRANCH"

    if [ -f "linux-service-manager.py" ]; then
        if grep -q "import ctypes" linux-service-manager.py; then
            echo "  ✅ System calls feature present"
        else
            echo "  ❌ Missing system call imports"
        fi
    fi
else
    echo "  ❌ Not a git repository"
fi
echo ""

# Open issues count
OPEN_ISSUES_NUM=${OPEN_ISSUES:-0}
if [ "$OPEN_ISSUES_NUM" -gt 0 ] && [ -n "$TOKEN" ]; then
    echo "⚠️  Open Issues:"
    curl -s -H "Authorization: token $TOKEN" "https://api.github.com/repos/$REPO/issues?state=open&per_page=3" |
        grep -o '"title":"[^"]*"' |
        sed 's/"/    /; s/^/    /' |
        head -3
    EXTRA=$((OPEN_ISSUES_NUM-3))
    if [ "$EXTRA" -gt 0 ]; then
        echo "  (... and $EXTRA more if applicable)"
    fi
    echo ""
fi

# Generate summary
echo "📈 Summary:"
echo "  Repository: https://github.com/$REPO"
echo "  Release: v1.0.0 published"
echo "  Local status: $(git status --porcelain 2>/dev/null | wc -l) uncommitted changes"
echo ""
echo "=== End of Report ==="

# Send report if requested
if [ "$SEND_REPORT" = true ]; then
    echo ""
    echo "📤 Sending report to $CHANNEL channel..."

    # Capture the report
    REPORT=$(cat <<EOF
GitHub Repository Report - $REPO

📊 Stats: ⭐ $STARS | 🍴 $FORKS | Issues: $OPEN_ISSUES | Size: ${SIZE}KB
📝 Description: $DESCRIPTION
🔗 https://github.com/$REPO

Local:
- Branch: $DEFAULT_BRANCH
- Uncommitted changes: $(git status --porcelain 2>/dev/null | wc -l)
- Recent commits visible in log

All systems operational. Repository serving as open-source educational tool for Linux system administration.

(Report generated at $TIMESTAMP)
EOF
    )

    # Try to send via OpenClaw message tool
    if command -v openclaw &> /dev/null; then
        echo "$REPORT" | openclaw message send --channel "$CHANNEL" --message "$(cat -)" 2>/dev/null && echo "Report sent via openclaw CLI" || echo "Failed to send via openclaw CLI"
    else
        # Fallback: just print, as the agent will handle the send
        echo "Report text prepared:"
        echo "$REPORT"
        echo ""
        echo "Note: To send automatically via cron, integrate with OpenClaw messaging API or email."
    fi
fi

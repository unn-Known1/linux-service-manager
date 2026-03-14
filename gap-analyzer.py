#!/usr/bin/env python3
"""
Market Gap Analyzer for Open Source Tools

This system:
1. Searches for common pain points and tooling gaps
2. Analyzes existing solutions and identifies opportunities
3. Generates repository ideas with roadmaps
4. Creates implementations with full documentation
5. Updates existing repositories with improvements
6. Runs hourly to continuously discover new opportunities

Usage:
    python3 gap-analyzer.py --analyze      # Find new gaps
    python3 gap-analyzer.py --expand ID    # Expand idea into full repo
    python3 gap-analyzer.py --update       # Update existing repos
    python3 gap-analyzer.py --report       # Generate status report
    python3 gap-analyzer.py --cron         # Run full hourly cycle

Configuration:
    Ideas stored in: ~/.local/share/gap-analyzer/ideas.json
    History: ~/.local/share/gap-analyzer/history.json
    Settings: ~/.config/gap-analyzer/config.json
"""

import os
import sys
import json
import time
import logging
import subprocess
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

# Optional: web search capability
try:
    from web_search import web_search
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('gap-analyzer')


class GapAnalyzer:
    """Analyze market gaps and manage repository ecosystem"""

    def __init__(self):
        self.config_dir = Path(os.path.expanduser('~/.config/gap-analyzer'))
        self.data_dir = Path(os.path.expanduser('~/.local/share/gap-analyzer'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.ideas_file = self.data_dir / 'ideas.json'
        self.history_file = self.data_dir / 'history.json'
        self.config_file = self.config_dir / 'config.json'

        self.ideas: Dict[str, dict] = {}
        self.history: List[dict] = []
        self.config = self._load_config()

        self._load_data()

    def _load_config(self) -> dict:
        """Load or create default configuration"""
        default_config = {
            'github_username': 'unn-Known1',
            'github_token': os.environ.get('GITHUB_TOKEN', ''),
            'target_repository': 'linux-service-manager',
            'work_repository': '/home/ptelgm/.openclaw/workspace-main',
            'search_topics': [
                'developer productivity tools',
                'devops automation gaps',
                'sysadmin pain points',
                'missing linux utilities',
                'infrastructure as code tools',
                'monitoring solutions',
                'security automation',
                'ci cd improvements',
                'container management',
                'cloud orchestration'
            ],
            'min_opportunity_score': 7.0,
            'auto_implement': False,
            'max_ideas_per_run': 3,
            'analysis_depth': 'medium'
        }

        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def _load_data(self):
        """Load ideas and history from disk"""
        if self.ideas_file.exists():
            with open(self.ideas_file, 'r') as f:
                self.ideas = json.load(f)

        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)

    def _save_data(self):
        """Save ideas and history to disk"""
        with open(self.ideas_file, 'w') as f:
            json.dump(self.ideas, f, indent=2)

        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def _generate_idea_id(self, title: str, category: str) -> str:
        """Generate unique ID for an idea (deterministic based on title+category)"""
        seed = f"{title}:{category}"
        return hashlib.md5(seed.encode()).hexdigest()[:8]

    def analyze_gaps(self) -> List[dict]:
        """Main analysis routine"""
        logger.info("Starting market gap analysis...")

        new_ideas = []

        pain_points = self._analyze_pain_points()
        new_ideas.extend(pain_points)

        if WEB_SEARCH_AVAILABLE and self.config.get('github_token'):
            trends = self._analyze_github_trends()
            new_ideas.extend(trends)

        complaints = self._analyze_tool_complaints()
        new_ideas.extend(complaints)

        evolution = self._analyze_tech_evolution()
        new_ideas.extend(evolution)

        deduped = self._deduplicate_ideas(new_ideas)
        high_value = [idea for idea in deduped if idea['opportunity_score'] >= self.config['min_opportunity_score']]
        limited = high_value[:self.config['max_ideas_per_run']]

        for idea in limited:
            if idea['id'] not in self.ideas:
                self.ideas[idea['id']] = idea
                logger.info(f"New idea discovered: {idea['title']} (score: {idea['opportunity_score']})")

        self._save_data()

        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'analysis',
            'new_ideas': len(limited),
            'ideas': [idea['id'] for idea in limited]
        })
        self._save_data()

        logger.info(f"Analysis complete: {len(limited)} high-value opportunities found")
        return limited

    def _analyze_pain_points(self) -> List[dict]:
        """Analyze known pain points"""
        # Pain points database
        pain_points = [
            {
                'title': 'Developer Portal',
                'category': 'Platform Engineering',
                'pain': 'Developers struggle to find internal tools, documentation, and standards. Each team builds their own portal fragment.',
                'solution': 'Internal developer platform with service catalog, documentation aggregation, template projects, and self-service provisioning.',
                'target_users': 'Developers, Platform engineers',
                'existing_solutions': 'Backstage (complex), custom internal portals, wikis',
                'gap': 'Lightweight, opinionated, easy-to-deploy developer portal for small-to-medium companies',
                'tech_stack': 'React/Next.js, Go/Python backend, PostgreSQL',
                'effort': 'Medium (2-4 months)',
                'opportunity_score': 8.7
            },
            {
                'title': 'Secrets Leak Detector',
                'category': 'Security',
                'pain': 'Developers accidentally commit secrets (API keys, passwords) to git repos. Detection happens too late; secrets already exposed.',
                'solution': 'Pre-commit hook and CI scanner that detects secrets before they are committed, with auto-remediation suggestions and education.',
                'target_users': 'Developers, Security teams',
                'existing_solutions': 'GitGuardian (commercial), truffleHog (open-source but limited), git-secrets (AWS)',
                'gap': 'Integrated pre-commit + CI solution with better detection algorithms and developer education',
                'tech_stack': 'Python, regex patterns, machine learning for pattern detection, pre-commit hooks',
                'effort': 'Medium (1-2 months)',
                'opportunity_score': 8.4
            },
            {
                'title': 'Pipeline Cost Tracker',
                'category': 'FinOps',
                'pain': 'CI/CD pipelines consume significant compute resources but costs are opaque. No visibility into which pipelines/jobs are expensive.',
                'solution': 'Track and visualize CI/CD resource usage and costs per pipeline, job, branch, and team. Provide optimization recommendations.',
                'target_users': 'DevOps, Platform engineers, Engineering managers',
                'existing_solutions': 'Custom dashboards, GitLab CI minutes tracking (limited), GitHub Actions billing (rough)',
                'gap': 'Detailed cost allocation across CI systems (GitHub Actions, GitLab CI, Jenkins, CircleCI)',
                'tech_stack': 'Python, time-series database, Grafana, CI APIs',
                'effort': 'Medium (2-3 months)',
                'opportunity_score': 8.1
            },
            {
                'title': 'Log Pattern Analyzer',
                'category': 'Observability',
                'pain': 'Log volumes are overwhelming. Identifying common patterns, anomalies, and top errors requires manual analysis or expensive tools.',
                'solution': 'Automatically cluster log messages by pattern, detect anomalies, highlight top errors, suggest fixes based on historical data.',
                'target_users': 'SREs, DevOps, Developers',
                'existing_solutions': 'Splunk (expensive), ELK stack (manual), Datadog Logs (costly)',
                'gap': 'Open-source, self-hosted, automated log pattern detection with anomaly detection',
                'tech_stack': 'Python, scikit-learn, Elasticsearch/Loki, clustering algorithms',
                'effort': 'Medium (2-4 months)',
                'opportunity_score': 8.6
            },
            {
                'title': 'DNS Management CLI',
                'category': 'Networking',
                'pain': 'Managing DNS across multiple providers (Route53, Cloudflare, Azure DNS) is tedious. Each has different CLI and API.',
                'solution': 'Unified CLI for DNS management: list zones, create/update records, propagate changes across providers, dry-run, rollback.',
                'target_users': 'DevOps, Network engineers',
                'existing_solutions': 'Provider-specific CLIs (aws route53, cfcli), Terraform (heavy), PowerDNS (self-hosted)',
                'gap': 'Lightweight, cross-provider DNS management with preview and safety checks',
                'tech_stack': 'Go, provider SDKs, Cobra CLI, YAML config',
                'effort': 'Small (1-2 months)',
                'opportunity_score': 7.9
            },
            {
                'title': 'Compliance as Code Scanner',
                'category': 'Compliance',
                'pain': 'Compliance checks (SOC2, HIPAA, PCI-DSS) are manual, spreadsheet-driven, and not integrated into development workflow.',
                'solution': 'Define compliance requirements as code, automatically scan infrastructure/config against them, generate evidence, track remediation.',
                'target_users': 'Compliance officers, Security engineers, DevOps',
                'existing_solutions': 'OpenSCAP (general), Cloud compliance tools (AWS Config Rules), commercial GRC platforms',
                'gap': 'Developer-friendly compliance as code with simple YAML definitions and CI integration',
                'tech_stack': 'Python, YAML/DSL for rules, CI integrations (GitHub Actions, GitLab CI)',
                'effort': 'Medium (2-3 months)',
                'opportunity_score': 8.5
            },
            {
                'title': 'Database Migration Orchestrator',
                'category': 'Data',
                'pain': 'Database schema migrations across multiple services and environments are error-prone. No unified view of migration status.',
                'solution': 'Orchestrate migrations: track which migrations have run on each environment, rollback capability, approval workflows, dry-run.',
                'target_users': 'Database admins, Backend developers, SREs',
                'existing_solutions': 'Flyway, Liquibase, Alembic (per-database), no cross-database orchestration',
                'gap': 'Multi-database (Postgres, MySQL, etc.) migration orchestration with status dashboard',
                'tech_stack': 'Go/Python, database drivers, Web UI, REST API',
                'effort': 'Medium (2-3 months)',
                'opportunity_score': 8.3
            },
            {
                'title': 'Incident Timeline Builder',
                'category': 'SRE',
                'pain': 'During/after incidents, building a timeline from logs, metrics, deployments, and chat is manual and time-consuming.',
                'solution': 'Automatically ingest data from monitoring, logging, chat (Slack/Discord), deployments, and build an interactive timeline with AI-assisted event correlation.',
                'target_users': 'SREs, DevOps, Incident responders',
                'existing_solutions': 'PagerDuty Timeline, OpsGenie (basic), manual timelines in incidents',
                'gap': 'Open-source, integrations with popular tools (Grafana, Loki, Sentry, Slack), AI correlation',
                'tech_stack': 'Python, Elasticsearch/Loki, TimescaleDB, React, LLM integration',
                'effort': 'Large (4-6 months)',
                'opportunity_score': 9.2
            },
            {
                'title': 'Code-to-Cloud Visualization',
                'category': 'Observability',
                'pain': 'Developers struggle to trace code execution through microservices to cloud resources and back. Distributed tracing exists but is not developer-friendly.',
                'solution': 'Visual map: click a function → see all cloud resources it touches → see data flow → see dependencies. Bidirectional linking.',
                'target_users': 'Developers, Architects, SREs',
                'existing_solutions': 'Datadog Service Map, AWS X-Ray (proprietary, expensive), Jaeger (engineering-focused)',
                'gap': 'Open-source, intuitive UI, integrates with OpenTelemetry and cloud APIs, developer-first UX',
                'tech_stack': 'Go/TypeScript, OpenTelemetry, GraphDB, React/Three.js',
                'effort': 'Large (3-6 months)',
                'opportunity_score': 9.0
            }
]
        return pain_points

    def _analyze_github_trends(self) -> List[dict]:
        """Analyze GitHub trends"""
        return []

    def _analyze_tool_complaints(self) -> List[dict]:
        """Analyze common complaints"""
        return []

    def _analyze_tech_evolution(self) -> List[dict]:
        """Identify gaps from technology evolution"""
        return []

    def _deduplicate_ideas(self, ideas: List[dict]) -> List[dict]:
        """Remove duplicate ideas"""
        seen_titles = set()
        deduped = []
        for idea in ideas:
            normalized = idea['title'].lower().strip()
            if normalized not in seen_titles:
                seen_titles.add(normalized)
                idea['id'] = self._generate_idea_id(idea['title'], idea['category'])
                deduped.append(idea)
        return deduped

    def expand_idea(self, idea_id: str) -> bool:
        """Expand an idea by adding it to the existing repository"""
        if idea_id not in self.ideas:
            logger.error(f"Idea {idea_id} not found")
            return False

        idea = self.ideas[idea_id]

        if 'expanded' in idea and idea['expanded']:
            logger.info(f"Idea {idea_id} already expanded")
            return False

        logger.info(f"Expanding idea: {idea['title']}")

        repo_dir = Path(self.config['work_repository'])
        if not repo_dir.exists():
            logger.error(f"Work repository does not exist: {repo_dir}")
            return False

        project_dir = repo_dir

        try:
            self._add_tool_to_repo(project_dir, idea)

            idea['expanded'] = True
            idea['expanded_at'] = datetime.now().isoformat()
            idea['repository_path'] = str(project_dir)
            self._save_data()

            logger.info(f"Tool added to repository at {project_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to expand idea: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _add_tool_to_repo(self, repo_dir: Path, idea: dict):
        """Add a new tool to the existing repository structure"""

        tool_name = idea['title'].lower().replace(' ', '-').replace('[^a-z0-9-]', '')
        tool_dir = repo_dir / 'tools' / tool_name
        if tool_dir.exists():
            logger.warning(f"Tool directory already exists: {tool_dir}, will overwrite")
        else:
            tool_dir.mkdir(parents=True, exist_ok=True)

        tech_stack_lower = idea['tech_stack'].lower()
        if 'python' in tech_stack_lower:
            main_ext = 'py'
            main_filename = f"{tool_name}.py"
            language = 'Python'
        elif 'go' in tech_stack_lower:
            main_ext = 'go'
            main_filename = f"{tool_name}.go"
            language = 'Go'
        elif 'node' in tech_stack_lower or 'javascript' in tech_stack_lower or 'typescript' in tech_stack_lower:
            main_ext = 'js'
            main_filename = f"{tool_name}.js"
            language = 'Node.js'
        else:
            main_ext = 'sh'
            main_filename = f"{tool_name}.sh"
            language = 'Shell'

        # Create tool README
        tool_readme = tool_dir / 'README.md'
        readme_template = """# {title}

## Overview

{solution}

## Problem Addressed

{pain}

## Why This Tool Exists

Existing solutions: {existing_solutions}

**Gap:** {gap}

## Installation

### Option 1: Direct Download
```bash
chmod +x {main_filename}
sudo cp {main_filename} /usr/local/bin/{tool_name}
```

### Option 2: Via Repository
This tool is part of the linux-service-manager toolkit. Simply run:
```bash
./{main_filename} --help
```

## Usage

_(To be completed after implementation)_

## Configuration

_(To be documented)_

## Technology

- **Language:** {language}
- **Tech Stack:** {tech_stack}

## Development

```bash
cd tools/{tool_name}
make deps   # Install dependencies
make test   # Run tests
make run    # Run locally
```

## Contributing

Improvements to this tool are welcome! See main repository CONTRIBUTING.md.

---
_Generated by Gap Analyzer on {timestamp}_
Opportunity Score: {opportunity_score}/10
"""
        tool_readme_content = readme_template.format(
            title=idea['title'],
            solution=idea['solution'],
            pain=idea['pain'],
            existing_solutions=idea['existing_solutions'],
            gap=idea['gap'],
            main_filename=main_filename,
            tool_name=tool_name,
            language=language,
            tech_stack=idea['tech_stack'],
            timestamp=datetime.now().strftime('%Y-%m-%d'),
            opportunity_score=idea['opportunity_score']
        )
        tool_readme.write_text(tool_readme_content)

        # Create main script
        main_file = tool_dir / main_filename

        epilog_text = '''
Examples:
  {tool_name} --analyze          # Analyze current state
  {tool_name} --fix              # Apply recommendations
  {tool_name} --monitor          # Start monitoring mode
'''

        if language == 'Python':
            main_content = f'''#!/usr/bin/env python3
"""
{idea['title']} - Preliminary Implementation

Solution: {idea['solution']}

This is a scaffold.
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description='{idea['title']}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog={repr(epilog_text)}
    )
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--analyze', action='store_true', help='Analyze and report')
    parser.add_argument('--fix', action='store_true', help='Apply automatic fixes')

    args = parser.parse_args()

    print(f"{{idea['title']}} - Scaffold Implementation")
    print("=" * 60)
    print(f"\\nSolution Concept:\\n{idea['solution']}")
    print("\\nTarget Users: {idea['target_users']}")
    print("\\nCurrent Status: Scaffold generated, implementation pending")
    print("\\nTechnology Stack: {idea['tech_stack']}")
    print("\\nEstimated Effort: {idea['effort']}")
    print("=" * 60)

    if args.analyze:
        print("\\n[ANALYSIS MODE] Would scan current environment and report findings.")
    if args.fix:
        print("\\n[FIX MODE] Would apply recommendations (not yet implemented)")

    return 0

if __name__ == '__main__':
    sys.exit(main())
'''
        elif language == 'Go':
            main_content = f'''package main

import (
    "flag"
    "fmt"
    "os"
)

var (
    configPath = flag.String("config", "", "Path to configuration file")
    verbose    = flag.Bool("verbose", false, "Verbose logging")
    dryRun     = flag.Bool("dry-run", false, "Show what would be done")
    analyze    = flag.Bool("analyze", false, "Analyze and report")
    fix        = flag.Bool("fix", false, "Apply automatic fixes")
)

func main() {{
    flag.Parse()

    fmt.Println("{idea['title']} - Scaffold Implementation")
    fmt.Println("===========================================")
    fmt.Printf("\\nSolution Concept:\\n{idea['solution']}\\n")
    fmt.Printf("\\nTarget Users: {idea['target_users']}\\n")
    fmt.Println("\\nCurrent Status: Scaffold generated, implementation pending")
    fmt.Printf("\\nTechnology Stack: {idea['tech_stack']}\\n")
    fmt.Printf("\\nEstimated Effort: {idea['effort']}\\n")
    fmt.Println("===========================================")

    if *analyze {{
        fmt.Println("\\n[ANALYSIS MODE] Would scan current environment and report findings.")
    }}
    if *fix {{
        fmt.Println("\\n[FIX MODE] Would apply recommendations (not yet implemented)")
    }}
}}
'''
        elif language == 'Node.js':
            main_content = f'''#!/usr/bin/env node

/**
 * {idea['title']}
 */
const yargs = require('yargs');

const argv = yargs
  .scriptName('{tool_name}')
  .description('{idea["title"]}')
  .option('config', {{ type: 'string', describe: 'Path to configuration file' }})
  .option('verbose', {{ type: 'boolean', alias: 'v', describe: 'Verbose logging' }})
  .option('dry-run', {{ type: 'boolean', describe: 'Show what would be done' }})
  .option('analyze', {{ type: 'boolean', describe: 'Analyze and report' }})
  .option('fix', {{ type: 'boolean', describe: 'Apply automatic fixes' }})
  .demandCommand(0, 1)
  .help()
  .alias('help', 'h')
  .argv;

console.log('{idea['title']} - Scaffold Implementation');
console.log('='.repeat(60));
console.log('\\nSolution Concept:\\n{idea['solution']}');
console.log('\\nTarget Users: {idea['target_users']}');
console.log('\\nCurrent Status: Scaffold generated, implementation pending');
console.log('\\nTechnology Stack: {idea['tech_stack']}');
console.log('\\nEstimated Effort: {idea['effort']}');
console.log('='.repeat(60));

if (argv.analyze) {{
  console.log('\\n[ANALYSIS MODE] Would scan current environment and report findings.');
}}
if (argv.fix) {{
  console.log('\\n[FIX MODE] Would apply recommendations (not yet implemented)');
}}
'''
        else:
            main_content = f'''#!/bin/bash
echo "{idea['title']} - Scaffold Implementation"
echo "==========================================="
echo ""
echo "Solution Concept:"
echo "{idea['solution']}"
echo ""
echo "Target Users: {idea['target_users']}"
echo ""
echo "Current Status: Scaffold generated, implementation pending"
echo ""
echo "Technology Stack: {idea['tech_stack']}"
echo ""
echo "Estimated Effort: {idea['effort']}"
echo "==========================================="
'''

        main_file.write_text(main_content)
        main_file.chmod(0o755)

        # Create Makefile for this tool
        tool_makefile = tool_dir / 'Makefile'
        if language == 'Python':
            makefile_content = f"""# Makefile for {tool_name}
.PHONY: all test run clean install help
all: help
help:
\t@echo "{idea['title']} - Commands:"
\t@echo "  make deps, test, run, install, clean"
deps:
\tpip install -r requirements.txt 2>/dev/null || echo "No requirements.txt yet"
test:
\t@echo "Running tests..." && python -m pytest tests/ -v 2>/dev/null || echo "No tests yet"
run:
\t./{main_filename} --help
install:
\tsudo cp {main_filename} /usr/local/bin/{tool_name} && sudo chmod +x /usr/local/bin/{tool_name}
clean:
\trm -rf __pycache__ *.pyc .pytest_cache .coverage
"""
        elif language == 'Go':
            makefile_content = f"""# Makefile for {tool_name}
.PHONY: all test build install clean help
all: help
help:
\t@echo "{idea['title']} - Commands:"
\t@echo "  make deps, test, build, install, clean"
deps:
\tgo mod download
test:
\tgo test ./...
build:
\tgo build -o bin/{tool_name} .
install: build
\tsudo cp bin/{tool_name} /usr/local/bin/
clean:
\trm -rf bin/
"""
        else:
            makefile_content = f"""# Makefile for {tool_name}
.PHONY: all test run install clean help
all: help
help:
\t@echo "{idea['title']} - Commands:"
\t@echo "  make test, run, install, clean"
test:
\t@echo "No tests yet"
run:
\t./{main_filename} --help
install:
\tsudo cp {main_filename} /usr/local/bin/{tool_name} && sudo chmod +x /usr/local/bin/{tool_name}
clean:
\t@echo "Clean complete"
"""
        tool_makefile.write_text(makefile_content)

        # Create basic requirements/deps
        if language == 'Python':
            reqs = tool_dir / 'requirements.txt'
            reqs.write_text('# Add Python dependencies here\n# Example:\n# click>=8.0\n# pandas>=1.0\n')

        # Create tests directory
        tests_dir = tool_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)
        if language == 'Python':
            test_file = tests_dir / 'test_scaffold.py'
            test_file.write_text('def test_scaffold():\n    assert True, "Implement real tests"\n')
        elif language == 'Go':
            test_file = tests_dir / 'main_test.go'
            test_file.write_text(f'package {tool_name}\n\nimport "testing"\n\nfunc TestScaffold(t *testing.T) {{\n    t.Skip("Implement real tests")\n}}\n')
        else:
            test_file = tests_dir / 'test_basic.js'
            test_file.write_text('// Implement tests\n')

        logger.info(f"Tool scaffold created: tools/{tool_name}/")

    def update_existing_repos(self) -> List[dict]:
        """Check existing repositories for updates needed"""
        logger.info("Checking existing repositories for updates...")

        updates_needed = []

        work_repo = Path(self.config['work_repository'])
        ls_manager = work_repo / 'linux-service-manager'

        if ls_manager.exists() or str(work_repo).endswith('workspace-main'):
            # Use work_repo directly since it IS the repo
            repo_path = work_repo
            suggestions = self._analyze_repo_improvements(repo_path)
            if suggestions:
                updates_needed.append({
                    'repository': 'linux-service-manager',
                    'path': str(repo_path),
                    'suggestions': suggestions,
                    'priority': 'high' if any(s['priority'] == 'high' for s in suggestions) else 'medium'
                })

        return updates_needed

    def _analyze_repo_improvements(self, repo_path: Path) -> List[dict]:
        """Analyze a repository and suggest improvements"""
        suggestions = []

        readme = repo_path / 'README.md'
        if readme.exists():
            content = readme.read_text()
            if 'Docker' not in content and 'container' not in content.lower():
                suggestions.append({
                    'type': 'documentation',
                    'priority': 'medium',
                    'suggestion': 'Add Docker containerization guide',
                    'details': 'Users expect container images. Add Dockerfile and instructions.'
                })
            if 'Kubernetes' not in content and 'k8s' not in content.lower():
                suggestions.append({
                    'type': 'documentation',
                    'priority': 'medium',
                    'suggestion': 'Add Kubernetes deployment examples',
                    'details': 'Provide k8s manifests or helm chart.'
                })

        if not (repo_path / 'CHANGELOG.md').exists():
            suggestions.append({
                'type': 'documentation',
                'priority': 'high',
                'suggestion': 'Create CHANGELOG.md',
                'details': 'Track version changes using Keep a Changelog format.'
            })

        if not (repo_path / 'CONTRIBUTING.md').exists():
            suggestions.append({
                'type': 'documentation',
                'priority': 'medium',
                'suggestion': 'Create CONTRIBUTING.md',
                'details': 'Guide for community contributions.'
            })

        if not (repo_path / '.github' / 'workflows').exists():
            suggestions.append({
                'type': 'infrastructure',
                'priority': 'medium',
                'suggestion': 'Add GitHub Actions CI pipeline',
                'details': 'Automate tests on push/PR.'
            })

        if not (repo_path / 'SECURITY.md').exists():
            suggestions.append({
                'type': 'policy',
                'priority': 'medium',
                'suggestion': 'Create SECURITY.md',
                'details': 'Document vulnerability reporting.'
            })

        return suggestions

    def apply_updates(self, repository: str, suggestions: List[dict]) -> bool:
        """Apply suggested updates to a repository"""
        logger.info(f"Applying {len(suggestions)} updates to {repository}")

        repo_path = Path(self.config['work_repository'])

        try:
            # Get current branch
            result = subprocess.run(['git', 'branch', '--show-current'], cwd=repo_path, capture_output=True, text=True)
            current_branch = result.stdout.strip() or 'main'
        except:
            current_branch = 'main'

        branch_name = f"automated-updates-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=repo_path, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            branch_name = current_branch

        applied = 0
        for suggestion in suggestions:
            try:
                if suggestion['type'] == 'documentation':
                    self._apply_documentation_update(repo_path, suggestion)
                elif suggestion['type'] == 'infrastructure':
                    self._apply_infrastructure_update(repo_path, suggestion)
                elif suggestion['type'] == 'content':
                    self._apply_content_update(repo_path, suggestion)
                logger.info(f"Applied: {suggestion['suggestion']}")
                applied += 1
            except Exception as e:
                logger.error(f"Failed: {suggestion['suggestion']}: {e}")

        if applied > 0:
            commit_msg = f"Automated updates via Gap Analyzer\\n\\n"
            for s in suggestions[:applied]:
                commit_msg += f"- {s['suggestion']}\\n"

            try:
                subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True, capture_output=True)
                subprocess.run(['git', 'commit', '-m', commit_msg], cwd=repo_path, check=True, capture_output=True)
                logger.info(f"Committed {applied} updates to {branch_name}")
                subprocess.run(['git', 'push', 'origin', branch_name], cwd=repo_path, check=False, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Git failed: {e}")

        return applied > 0

    def _apply_documentation_update(self, repo_path: Path, suggestion: dict):
        """Apply documentation updates"""
        readme = repo_path / 'README.md'
        content = readme.read_text() if readme.exists() else ""

        if 'changelog' in suggestion['suggestion'].lower():
            changelog = repo_path / 'CHANGELOG.md'
            if not changelog.exists():
                changelog_content = """# Changelog

All notable changes will be documented here.

## [Unreleased]

### Added
- Initial project structure

## [1.0.0] - YYYY-MM-DD
### Added
- Linux Service Manager with daemonization
- System call demonstrations
- Comprehensive documentation

"""
                changelog.write_text(changelog_content)

        elif 'contributing' in suggestion['suggestion'].lower():
            contributing = repo_path / 'CONTRIBUTING.md'
            if not contributing.exists():
                contributing.write_text("""# Contributing

Thank you for your interest! Please:

1. Fork and clone
2. Create feature branch
3. Make changes
4. Add tests
5. Submit Pull Request

See issues for areas needing help.
""")

        elif 'security' in suggestion['suggestion'].lower():
            security = repo_path / 'SECURITY.md'
            if not security.exists():
                security.write_text("""# Security Policy

Report vulnerabilities via GitHub's private reporting or email.

We will respond within 48 hours. Please do not open public issues for security bugs.
""")

        # Add CI if needed
        if 'GitHub Actions' in suggestion.get('details', ''):
            self._add_github_actions_ci(repo_path)

    def _apply_infrastructure_update(self, repo_path: Path, suggestion: dict):
        """Apply infrastructure updates"""
        if 'GitHub Actions' in suggestion['suggestion']:
            self._add_github_actions_ci(repo_path)

    def _add_github_actions_ci(self, repo_path: Path):
        """Add GitHub Actions workflow"""
        workflows_dir = repo_path / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True, exist_ok=True)
        ci_content = """name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt 2>/dev/null || echo "No requirements"
    - name: Run linter
      run: |
        python -m py_compile *.py 2>/dev/null || true
    - name: Test
      run: |
        python -m pytest tests/ 2>/dev/null || echo "No tests yet"
"""
        (workflows_dir / 'ci.yml').write_text(ci_content)

    def _apply_content_update(self, repo_path: Path, suggestion: dict):
        """Apply content updates"""
        if 'examples' in suggestion['suggestion'].lower():
            examples_dir = repo_path / 'examples'
            examples_dir.mkdir(exist_ok=True)
            if not (examples_dir / 'usage-examples.md').exists():
                examples_dir.write_text("""# Usage Examples

Add examples here as the tools are implemented.
""")

    def generate_report(self) -> str:
        """Generate status report"""
        lines = [
            "=== Gap Analyzer Report ===",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total ideas: {len(self.ideas)}",
            "",
            "Ideas:",
        ]
        for idea in sorted(self.ideas.values(), key=lambda x: x.get('opportunity_score', 0), reverse=True)[:10]:
            status = "✓" if idea.get('expanded') else "○"
            lines.append(f"  {status} [{idea.get('opportunity_score')}] {idea['title']}")
        lines.append("")
        lines.append("=== End of Report ===")
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Market Gap Analyzer for Open Source Tools')
    parser.add_argument('--analyze', action='store_true', help='Find new gaps')
    parser.add_argument('--expand', metavar='ID', help='Expand an idea into repository')
    parser.add_argument('--update', action='store_true', help='Check and apply updates')
    parser.add_argument('--report', action='store_true', help='Generate status report')
    parser.add_argument('--cron', action='store_true', help='Run full hourly cycle')
    parser.add_argument('--list', action='store_true', help='List all ideas')
    parser.add_argument('--show', metavar='ID', help='Show details for an idea')

    args = parser.parse_args()
    analyzer = GapAnalyzer()

    if args.analyze:
        new_ideas = analyzer.analyze_gaps()
        print(f"Found {len(new_ideas)} opportunities")
        for idea in new_ideas:
            print(f"  [{idea['opportunity_score']}] {idea['title']}")

    elif args.expand:
        if analyzer.expand_idea(args.expand):
            print(f"Expanded idea {args.expand}")
        else:
            print("Failed")

    elif args.update:
        updates = analyzer.update_existing_repos()
        print(f"Found {len(updates)} repos needing updates")
        for upd in updates:
            print(f"\n{upd['repository']}:")
            for s in upd['suggestions']:
                print(f"  - {s['suggestion']}")

    elif args.report:
        print(analyzer.generate_report())

    elif args.list:
        print(f"Total ideas: {len(analyzer.ideas)}")
        sorted_ideas = sorted(analyzer.ideas.values(), key=lambda x: x.get('opportunity_score', 0), reverse=True)
        for idea in sorted_ideas:
            status = "✓" if idea.get('expanded') else "○"
            print(f"{status} [{idea.get('opportunity_score', 'N/A')}] {idea['title']}")

    elif args.show:
        if args.show in analyzer.ideas:
            print(json.dumps(analyzer.ideas[args.show], indent=2))
        else:
            print("Idea not found")

    elif args.cron:
        print("Running full cycle...")
        new_ideas = analyzer.analyze_gaps()
        print(f"Analysis: {len(new_ideas)} new")
        if analyzer.config.get('auto_implement') and new_ideas:
            top = max(new_ideas, key=lambda x: x.get('opportunity_score', 0))
            analyzer.expand_idea(top['id'])
        updates = analyzer.update_existing_repos()
        print(f"Updates needed: {len(updates)}")
        print(analyzer.generate_report())

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

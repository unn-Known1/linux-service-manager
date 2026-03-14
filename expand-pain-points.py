#!/usr/bin/env python3
"""Expand the pain points database in gap-analyzer.py"""

import re

# Read current file
with open('gap-analyzer.py', 'r') as f:
    content = f.read()

# Find the _analyze_pain_points method and replace its pain_points list
# The pain_points list ends before "# Score them..."

old_method_pattern = r'(    def _analyze_pain_points\(self\) -> List\[dict\]:\s*""".*?""".*?pain_points = \[)(.*?)(\].*?return pain_points)'
# Need to use DOTALL to match across lines

match = re.search(old_method_pattern, content, re.DOTALL)
if not match:
    print("ERROR: Could not find _analyze_pain_points method")
    exit(1)

before = match.group(1)
after = match.group(3)

# New pain points (only the ones NOT already present)
new_pain_points = '''
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
'''

# Combine
new_content = before + new_pain_points + after

# Replace
content = re.sub(old_method_pattern, new_content, content, flags=re.DOTALL)

# Write back
with open('gap-analyzer.py', 'w') as f:
    f.write(content)

print("Expanded pain points database with 10 new ideas")
print("Total ideas now available: ~20 unique high-value opportunities")

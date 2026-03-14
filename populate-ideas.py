#!/usr/bin/env python3
"""Populate the gap analyzer database with all high-value ideas"""

import json
import hashlib
from datetime import datetime

IDEAS = [
    # Original top tools - already expanded
    {
        'title': 'Multi-Cloud Cost Optimizer',
        'category': 'Cloud Finance',
        'pain': 'Companies using multiple cloud providers lack unified cost visibility and optimization. Each provider has different pricing models and tools.',
        'solution': 'Tool that aggregates costs across AWS/Azure/GCP, provides recommendations, and can automatically implement savings (right-sizing, reserved instances, spot instances).',
        'target_users': 'DevOps engineers, FinOps teams, Cloud architects',
        'existing_solutions': 'CloudHealth, CloudCheckr (expensive), manual spreadsheets',
        'gap': 'Open-source, self-hosted alternative with API-first design',
        'tech_stack': 'Python, Click, Pandas, Cloud SDKs, React dashboard',
        'effort': 'Large (3-6 months)',
        'opportunity_score': 9.0,
        'expanded': True,
        'repository_path': '/home/ptelgm/.openclaw/workspace-main/tools/multi-cloud-cost-optimizer'
    },
    {
        'title': 'Secret Rotation Orchestrator',
        'category': 'Security',
        'pain': 'Rotating secrets (database passwords, API keys, certificates) is security best practice but manually risky and operationally complex.',
        'solution': 'Orchestrate secret rotation across systems: generate new secrets, update dependent services atomically, handle rollback, maintain audit trail.',
        'target_users': 'Security engineers, DevOps',
        'existing_solutions': 'HashiCorp Vault (rotation custom), AWS Secrets Manager (AWS only), CyberArk (enterprise)',
        'gap': 'Multi-cloud, open-source, GitOps-friendly approach with clear audit logs',
        'tech_stack': 'Go, BoltDB/PostgreSQL, gRPC, Web UI',
        'effort': 'Medium (2-4 months)',
        'opportunity_score': 8.8,
        'expanded': True,
        'repository_path': '/home/ptelgm/.openclaw/workspace-main/tools/secret-rotation-orchestrator'
    },
    {
        'title': 'Infrastructure Drift Detector',
        'category': 'IaC',
        'pain': 'IaC tools (Terraform, CloudFormation) define desired state, but actual infrastructure can drift due to manual changes, emergencies, or bugs.',
        'solution': 'Continuous drift detection that compares live infrastructure against IaC definitions, alerts on discrepancies, and can auto-remediate.',
        'target_users': 'DevOps, Platform engineers',
        'existing_solutions': 'AWS Config, Azure Policy (cloud-specific), drift detection in commercial tools',
        'gap': 'Vendor-neutral, supports multiple IaC tools and cloud providers',
        'tech_stack': 'Go/Python, Terraform SDK, Cloud SDKs, Notifications',
        'effort': 'Medium (2-3 months)',
        'opportunity_score': 8.5,
        'expanded': True,
        'repository_path': '/home/ptelgm/.openclaw/workspace-main/tools/infrastructure-drift-detector'
    },
    # Remaining high-value ideas - not yet expanded
    {
        'title': 'Kubernetes Cost Allocation',
        'category': 'FinOps',
        'pain': 'K8s clusters share resources among teams/projects, but charging back costs is difficult. Tools like OpenCost exist but need better multi-cluster support.',
        'solution': 'Detailed cost allocation per namespace, label, or team across multiple clusters. Integrate with billing APIs and provide chargeback reports.',
        'target_users': 'Platform engineers, FinOps, Product teams',
        'existing_solutions': 'OpenCost, Kubecost (commercial features), custom scripts',
        'gap': 'Better multi-cluster aggregation, simpler deployment, more cloud provider integrations',
        'tech_stack': 'Go, Prometheus, TimescaleDB, Grafana dashboards',
        'effort': 'Medium (2-3 months)',
        'opportunity_score': 8.2
    },
    {
        'title': 'Serverless Testing Framework',
        'category': 'Testing',
        'pain': 'Testing serverless functions (AWS Lambda, Azure Functions) locally is hard due to event sources, triggers, and cloud dependencies. LocalStack helps but lacks full testing workflow.',
        'solution': 'Testing framework specifically for serverless: local event simulation, integration testing, fixture management, and CI/CD integration.',
        'target_users': 'Serverless developers, Backend engineers',
        'existing_solutions': 'LocalStack (emulation), SAM CLI, Serverless Framework testing (basic)',
        'gap': 'Comprehensive testing utilities: mocks, integration tests, load testing, contract verification',
        'tech_stack': 'Node.js/Python, Docker, Testing frameworks (Jest/pytest)',
        'effort': 'Medium (2-3 months)',
        'opportunity_score': 8.0
    },
    {
        'title': 'Configuration Drift Remediation',
        'category': 'Configuration Management',
        'pain': 'Configuration management tools (Ansible, Chef, Puppet) detect drift but often require manual intervention or re-running full playbooks.',
        'solution': 'Automated, selective remediation: only fix what drifted, with change approval workflows and dry-run capabilities.',
        'target_users': 'Sysadmins, Configuration managers',
        'existing_solutions': 'Ansible --check mode, Rudder (commercial), custom scripts',
        'gap': 'Open-source, policy-as-code approach with selective remediation and approval gates',
        'tech_stack': 'Python, Ansible modules, Git integration, Notification systems',
        'effort': 'Medium (1-2 months)',
        'opportunity_score': 7.8
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
    },
    # Newly added ones from expand-pain-points.py (some already in list above, ensure unique)
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
    }
]

def generate_id(title, category):
    seed = f"{title}:{category}"
    return hashlib.md5(seed.encode()).hexdigest()[:8]

# Load existing database
ideas_file = '/home/ptelgm/.local/share/gap-analyzer/ideas.json'
try:
    with open(ideas_file, 'r') as f:
        ideas = json.load(f)
except FileNotFoundError:
    ideas = {}

# Add all ideas (will not overwrite existing)
for idea in IDEAS:
    idea_id = generate_id(idea['title'], idea['category'])
    if idea_id in ideas:
        print(f"Skipping existing: {idea['title']}")
    else:
        idea_copy = idea.copy()
        idea_copy['id'] = idea_id
        if 'expanded_at' not in idea_copy and idea_copy.get('expanded'):
            idea_copy['expanded_at'] = datetime.now().isoformat()
        ideas[idea_id] = idea_copy
        print(f"Added: {idea['title']} (score {idea['opportunity_score']})")

# Save
with open(ideas_file, 'w') as f:
    json.dump(ideas, f, indent=2)

print(f"\nTotal ideas in database: {len(ideas)}")
print("Done!")

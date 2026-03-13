#!/usr/bin/env python3
"""
Update the main README with a catalog of all tools in the repository
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def discover_tools(repo_dir: Path) -> list:
    """Discover all tools in the tools/ directory"""
    tools = []
    tools_dir = repo_dir / 'tools'

    if not tools_dir.exists():
        return tools

    for tool_dir in tools_dir.iterdir():
        if tool_dir.is_dir():
            readme = tool_dir / 'README.md'
            main_file = None
            for f in tool_dir.iterdir():
                if f.name.endswith('.py') or f.name.endswith('.go') or f.name.endswith('.js') or f.name.endswith('.sh'):
                    main_file = f
                    break

            if readme.exists() and main_file:
                # Extract description from README
                content = readme.read_text()
                lines = content.split('\n')
                description = ""
                for line in lines[1:10]:  # Look in first few lines after title
                    if line.strip() and not line.startswith('#'):
                        description = line.strip()
                        break

                tools.append({
                    'name': tool_dir.name,
                    'display_name': tool_dir.name.replace('-', ' ').title(),
                    'path': str(tool_dir.relative_to(repo_dir)),
                    'description': description[:200] if description else "Tool description pending...",
                    'main_file': main_file.name,
                    'readme': readme
                })

    return sorted(tools, key=lambda x: x['name'])

def generate_tools_section(tools: list) -> str:
    """Generate the Tools section for README"""

    section = """## 🛠️ Toolkit

This repository has evolved into a **Linux DevOps Toolkit** with multiple specialized utilities.

### Available Tools

| Tool | Description | Status |
|------|-------------|--------|
"""

    for tool in tools:
        status = "✅ Ready" if "Scaffold" not in tool['description'] else "🚧 Scaffold"
        section += f"| [`{tool['name']}`](tools/{tool['name']}/README.md) | {tool['description']} | {status} |\n"

    section += """
### Using a Tool

Each tool is self-contained in its own directory:

```bash
# See help for a specific tool
./tools/<tool-name>/<main-file> --help

# Or install it system-wide
cd tools/<tool-name>
sudo make install
```

### Development

Tools are automatically generated scaffolds based on market gap analysis.
See [Gap Analyzer](gap-analyzer.py) for how new tools are created.

"""
    return section

def update_readme(repo_dir: Path):
    """Update the main README with tools catalog"""

    readme_path = repo_dir / 'README.md'
    if not readme_path.exists():
        print(f"ERROR: README.md not found at {readme_path}")
        return False

    original_content = readme_path.read_text()

    # Find the position to insert tools section
    # Insert after the "Quick Start" section or after "Features"
    insert_marker = "## Quick Start"
    if insert_marker not in original_content:
        insert_marker = "## Features"
        if insert_marker not in original_content:
            print("Cannot find insertion point")
            return False

    insert_pos = original_content.find(insert_marker)
    if insert_pos == -1:
        return False

    # Find end of that section (next ## or end of file)
    next_section = original_content.find('\n## ', insert_pos + len(insert_marker))
    if next_section == -1:
        next_section = len(original_content)

    # Insert our tools section
    tools = discover_tools(repo_dir)
    tools_section = generate_tools_section(tools)

    new_content = (
        original_content[:next_section] +
        '\n' + tools_section +
        original_content[next_section:]
    )

    readme_path.write_text(new_content)
    print(f"Updated README.md with {len(tools)} tools")
    return True

def main():
    repo_dir = Path('/home/ptelgm/.openclaw/workspace-main')
    if len(sys.argv) > 1:
        repo_dir = Path(sys.argv[1])

    if update_readme(repo_dir):
        print("README updated successfully")
        return 0
    else:
        print("Failed to update README")
        return 1

if __name__ == '__main__':
    sys.exit(main())

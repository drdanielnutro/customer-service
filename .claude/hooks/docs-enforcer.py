#!/usr/bin/env python3
import json
import sys
import re

# Domínio da documentação ADK
DOCS_BASE_URL = "google.github.io/adk-docs"
DOCS_PATTERN = r"https?://google\.github\.io/adk-docs"

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

# Para WebSearch - forçar domínio específico
if tool_name == "WebSearch":
    allowed_domains = tool_input.get("allowed_domains", [])
    
    # Se não tem allowed_domains ou não inclui nosso domínio
    if not allowed_domains or DOCS_BASE_URL not in str(allowed_domains):
        print(f"ADK Documentation search must use allowed_domains: ['{DOCS_BASE_URL}']", file=sys.stderr)
        sys.exit(2)

# Para WebFetch - garantir que é do domínio correto
elif tool_name == "WebFetch":
    url = tool_input.get("url", "")
    
    # Verificar se a URL é do domínio ADK docs
    if not re.match(DOCS_PATTERN, url):
        print(f"URL must be from ADK documentation at {DOCS_BASE_URL}", file=sys.stderr)
        print(f"Requested URL '{url}' is outside the ADK docs domain", file=sys.stderr)
        sys.exit(2)
    
    # Auto-aprovar URLs da documentação ADK
    output = {
        "decision": "approve",
        "reason": "ADK documentation URL auto-approved",
        "suppressOutput": True
    }
    print(json.dumps(output))
    sys.exit(0)

# Permitir outras ferramentas
sys.exit(0)
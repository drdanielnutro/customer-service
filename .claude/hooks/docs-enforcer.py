#!/usr/bin/env python3
import json
import sys
import re

# Domínios permitidos para documentação oficial
ADK_DOCS_URL = "google.github.io/adk-docs"
GEMINI_API_URL = "ai.google.dev"
ALLOWED_DOMAINS = [ADK_DOCS_URL, GEMINI_API_URL]

# Padrões para validação de URLs
ADK_PATTERN = r"https?://google\.github\.io/adk-docs"
GEMINI_PATTERN = r"https?://ai\.google\.dev"
ALLOWED_PATTERNS = [ADK_PATTERN, GEMINI_PATTERN]

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

# Para WebSearch - verificar domínios permitidos
if tool_name == "WebSearch":
    allowed_domains = tool_input.get("allowed_domains", [])
    
    # Verificar se pelo menos um domínio permitido está presente
    has_allowed_domain = any(domain in str(allowed_domains) for domain in ALLOWED_DOMAINS)
    
    if not allowed_domains or not has_allowed_domain:
        print(f"Search must use allowed_domains with at least one of: {ALLOWED_DOMAINS}", file=sys.stderr)
        print(f"Current allowed_domains: {allowed_domains}", file=sys.stderr)
        sys.exit(2)

# Para WebFetch - garantir que é de domínio permitido
elif tool_name == "WebFetch":
    url = tool_input.get("url", "")
    
    # Verificar se a URL corresponde a algum padrão permitido
    is_allowed = any(re.match(pattern, url) for pattern in ALLOWED_PATTERNS)
    
    if not is_allowed:
        print(f"URL must be from official documentation domains: {ALLOWED_DOMAINS}", file=sys.stderr)
        print(f"Requested URL '{url}' is outside allowed domains", file=sys.stderr)
        sys.exit(2)
    
    # Auto-aprovar URLs de documentação oficial
    if re.match(ADK_PATTERN, url):
        reason = "ADK documentation URL auto-approved"
    elif re.match(GEMINI_PATTERN, url):
        reason = "Gemini API documentation URL auto-approved"
    else:
        reason = "Official documentation URL auto-approved"
    
    output = {
        "decision": "approve",
        "reason": reason,
        "suppressOutput": True
    }
    print(json.dumps(output))
    sys.exit(0)

# Permitir outras ferramentas
sys.exit(0)
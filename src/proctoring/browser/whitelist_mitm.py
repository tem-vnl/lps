from mitmproxy import http, ctx
import re
import os

def format_domain_pattern(domain):
    # Escape dots and convert domain to regex pattern
    escaped = domain.replace('.', r'\.')
    return f"(.*\.)?{escaped}$"

def load_patterns():
    patterns = []
    try:
        pattern_file = os.path.join(os.path.dirname(__file__), "whitelist.txt")
        with open(pattern_file, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
            patterns = [format_domain_pattern(domain) for domain in domains]
        ctx.log.info(f"Loaded {len(patterns)} whitelist patterns")
    except Exception as e:
        ctx.log.error(f"Failed to load whitelist patterns: {e}")
        # Fallback to empty list - block everything if file can't be read
        patterns = []
    return patterns

def is_whitelisted(host):
    return any(re.match(pattern, host) for pattern in WHITELIST_PATTERNS)

def request(flow: http.HTTPFlow) -> None:
    if not is_whitelisted(flow.request.pretty_host):
        flow.response = http.Response.make(
            403, b"Blocked by whitelist proxy, press alt+leftArrow to go back", {"Content-Type": "text/plain"}
        )

WHITELIST_PATTERNS = load_patterns()
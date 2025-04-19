from mitmproxy import http
import re

WHITELIST_PATTERNS = [
    r".*\.google\.com$",
    r".*\.googleapis\.com$",
    r".*\.gstatic\.com$",
    r".*chrome\.webdriver\.com$"
]

def is_whitelisted(host):
    return any(re.match(pattern, host) for pattern in WHITELIST_PATTERNS)

def request(flow: http.HTTPFlow) -> None:
    if not is_whitelisted(flow.request.pretty_host):
        flow.response = http.Response.make(
            403, b"Blocked by whitelist proxy", {"Content-Type": "text/plain"}
        )

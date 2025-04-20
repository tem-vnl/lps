from mitmproxy import http
import re

WHITELIST_PATTERNS = [
    r"(.*\.)?canvas\.kth\.se$",
    r"(.*\.)?saml-5\.sys\.kth\.se$",
    r"(.*\.)?login\.ug\.kth\.se$",
    r"(.*\.)?sso\.canvaslms\.com$",
    r"(.*\.)?instructure\.com$", 
    r"(.*\.)?canvaslms\.com$",
    r"(.*\.)?kth\.se$",
    r".*chrome\.webdriver\.com$"
]

def is_whitelisted(host):
    return any(re.match(pattern, host) for pattern in WHITELIST_PATTERNS)

def request(flow: http.HTTPFlow) -> None:
    if not is_whitelisted(flow.request.pretty_host):
        flow.response = http.Response.make(
            403, b"Blocked by whitelist proxy, press alt+leftArrow to go back", {"Content-Type": "text/plain"}
        )

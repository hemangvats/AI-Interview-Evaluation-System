import re
import socket
import ipaddress
from urllib.parse import urlparse

# Private IP networks for SSRF protection
PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Cloud metadata IP
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

LINKEDIN_PROFILE_REGEX = re.compile(
    r"^https?://([a-zA-Z0-9\-]+\.)*linkedin\.com/in/[a-zA-Z0-9_\-%]+/?.*$",
    re.IGNORECASE
)

def validate_linkedin_url(url: str) -> str:
    """
    Strictly validates that a URL is a valid public LinkedIn profile URL.
    Returns cleaned canonical URL or raises ValueError.
    """
    if not url or not isinstance(url, str):
        raise ValueError("LinkedIn URL is required.")
        
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
        
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise ValueError("Invalid URL scheme. Only HTTP and HTTPS are allowed.")
        
    host = (parsed.hostname or "").lower()
    if not host.endswith("linkedin.com"):
        raise ValueError("Invalid URL. Only official LinkedIn URLs (linkedin.com/in/...) are accepted.")
        
    if not LINKEDIN_PROFILE_REGEX.match(url):
        raise ValueError("Invalid LinkedIn profile URL format. Example format: https://www.linkedin.com/in/username")
        
    return url

def verify_ssrf_safe(target_url: str) -> bool:
    """
    Server-side SSRF validation preventing outbound requests to private IPs,
    localhost, internal network endpoints, link-local, and cloud metadata.
    """
    try:
        parsed = urlparse(target_url)
        host = parsed.hostname
        if not host:
            return False
            
        host_lower = host.lower().strip("[]")
        if host_lower in ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "::1", "::"]:
            return False
            
        # Direct IP literal check
        try:
            ip_obj = ipaddress.ip_address(host_lower)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_unspecified:
                return False
            for private_net in PRIVATE_NETWORKS:
                if ip_obj in private_net:
                    return False
        except ValueError:
            pass

        # Resolve all DNS A/AAAA records
        addr_info = socket.getaddrinfo(host, None)
        for res in addr_info:
            ip_str = res[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_unspecified:
                return False
            for private_net in PRIVATE_NETWORKS:
                if ip_obj in private_net:
                    return False
                
        return True
    except Exception:
        return False


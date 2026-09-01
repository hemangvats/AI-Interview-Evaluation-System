import re
import socket
import ipaddress
from urllib.parse import urlparse

PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9\-_]{1,39}$")

def clean_github_input(input_str: str) -> str:
    """
    Extracts and strictly validates a GitHub username from username string or URL.
    Returns cleaned valid username or raises ValueError.
    """
    if not input_str or not isinstance(input_str, str):
        raise ValueError("GitHub username or profile URL is required.")
        
    cleaned = input_str.strip().rstrip("/")
    
    # If full URL was provided
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        parsed = urlparse(cleaned)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Invalid URL scheme. Only HTTP and HTTPS are allowed.")
        host = (parsed.hostname or "").lower()
        if host not in ["github.com", "www.github.com", "api.github.com"]:
            raise ValueError("Invalid URL. Only official GitHub profile URLs (github.com/username) are accepted.")
        path_parts = [p for p in parsed.path.split("/") if p]
        if not path_parts:
            raise ValueError("Invalid GitHub profile URL.")
        cleaned = path_parts[0]
        
    if "github.com/" in cleaned:
        cleaned = cleaned.split("github.com/")[-1].split("/")[0]

    cleaned = cleaned.strip()
    if not USERNAME_REGEX.match(cleaned):
        raise ValueError("Invalid GitHub username format. Usernames contain alphanumeric characters or hyphens (1-39 chars).")

    return cleaned

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


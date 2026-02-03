from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    parsed = urlparse(url)
    return parsed.netloc

import asyncio
import datetime
import socket
import ssl
from bs4 import BeautifulSoup
from typing import List

try:
    import whois
except Exception:
    whois = None

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from .utils import extract_domain


def _get_domain_age_sync(domain: str):
    if whois:
        try:
            w = whois.whois(domain)
            cd = w.creation_date
            if isinstance(cd, list):
                cd = cd[0]
            if not cd:
                return None
            age_days = (datetime.datetime.now() - cd).days
            return age_days
        except Exception:
            return None
    return None


def _check_ssl_sync(domain: str):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                issuer = cert.get('issuer')
                if issuer:
                    for part in issuer:
                        for k, v in part:
                            if k.lower() in ('commonname', 'commonName', 'cn'):
                                return v
                    return str(issuer)
    except Exception:
        return None


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def _fetch_text(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url, timeout=6.0)
    resp.raise_for_status()
    return resp.text


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def _head_status(client: httpx.AsyncClient, url: str) -> int:
    try:
        resp = await client.head(url, follow_redirects=True, timeout=5.0)
        return resp.status_code
    except httpx.HTTPError:
        # treat as broken
        return 599


async def get_domain_age(domain: str):
    return await asyncio.to_thread(_get_domain_age_sync, domain)


async def check_ssl(domain: str):
    return await asyncio.to_thread(_check_ssl_sync, domain)


async def find_broken_social_links(url: str) -> List[str]:
    broken = []
    async with httpx.AsyncClient(headers={'User-Agent': 'hashtrack/1.0'}) as client:
        try:
            text = await _fetch_text(client, url)
            soup = BeautifulSoup(text, 'html.parser')
            tasks = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(s in href for s in ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'tiktok.com']):
                    tasks.append(_head_status(client, href))
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                idx = 0
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(s in href for s in ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'tiktok.com']):
                        status = results[idx]
                        idx += 1
                        try:
                            if isinstance(status, Exception) or status >= 400:
                                broken.append(href)
                        except Exception:
                            broken.append(href)
        except Exception:
            return []
    return broken


async def has_contact_info(url: str) -> bool:
    async with httpx.AsyncClient(headers={'User-Agent': 'hashtrack/1.0'}) as client:
        try:
            text = await _fetch_text(client, url)
            text = text.lower()
            return ('address' in text) or ('phone' in text) or ('contact' in text) or ('tel:' in text)
        except Exception:
            return False


async def contains_urgency_terms(url: str) -> bool:
    async with httpx.AsyncClient(headers={'User-Agent': 'hashtrack/1.0'}) as client:
        try:
            text = await _fetch_text(client, url)
            text = text.lower()
            for term in ['hurry', 'limited time', 'only', 'counter', 'order now', 'sale ends', 'while stocks last']:
                if term in text:
                    return True
        except Exception:
            return False
    return False


async def analyze_domain_async(url: str):
    domain = extract_domain(url)
    reasons = []
    score = 0

    # run checks concurrently
    age_task = asyncio.create_task(get_domain_age(domain))
    ssl_task = asyncio.create_task(check_ssl(domain))
    broken_task = asyncio.create_task(find_broken_social_links(url))
    contact_task = asyncio.create_task(has_contact_info(url))
    urgency_task = asyncio.create_task(contains_urgency_terms(url))

    age = await age_task
    if age is None:
        reasons.append('Domain age unknown')
    else:
        if age < 30:
            score += 40
            reasons.append(f'Domain created {age} days ago (<30 days)')
        elif age < 180:
            score += 15
            reasons.append(f'Domain created {age} days ago (<6 months)')

    issuer = await ssl_task
    if issuer:
        if "Let's Encrypt" in issuer or 'cPanel' in issuer:
            score += 10
            reasons.append(f'SSL issuer: {issuer}')
    else:
        reasons.append('No SSL or unable to fetch certificate')

    broken = await broken_task
    if broken:
        score += 25
        reasons.append('Broken social links')

    has_contact = await contact_task
    if not has_contact:
        score += 20
        reasons.append('Missing contact info')

    urgency = await urgency_task
    if urgency:
        score += 10
        reasons.append('Urgency/marketing terms detected')

    # Outdated copyright check
    try:
        async with httpx.AsyncClient(headers={'User-Agent': 'hashtrack/1.0'}) as client:
            text = await _fetch_text(client, url)
            if 'copyright 2023' in text.lower():
                score += 5
                reasons.append('Outdated copyright (2023)')
    except Exception:
        pass

    risk_level = 'SAFE' if score <= 20 else 'CAUTION' if score <= 50 else 'CRITICAL'
    trust_score = max(0, 100 - score)

    return {
        'domain': domain,
        'trust_score': trust_score,
        'risk_level': risk_level,
        'reasons': reasons
    }


# backward compatible sync wrapper
def analyze_domain(url: str):
    return asyncio.run(analyze_domain_async(url))

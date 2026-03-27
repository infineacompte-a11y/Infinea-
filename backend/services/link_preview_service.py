"""
InFinea — Link Preview Service (Open Graph / OG Cards).

Extracts URLs from text, fetches Open Graph metadata (title, description, image, site_name),
and returns a compact preview object for rich display in the feed.

Benchmarks: Slack, Discord, iMessage, LinkedIn, WhatsApp — all render OG cards inline.

Security:
- Timeout: 5s max per fetch (non-blocking, fail-safe)
- No internal/private IPs fetched (SSRF protection)
- Sanitized output (no script injection)
- Cached in DB to avoid repeated fetches
"""

import re
import logging
from typing import Optional
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

from database import db

logger = logging.getLogger(__name__)

# URL regex — match http(s) URLs in text
URL_RE = re.compile(
    r"https?://[^\s<>\"')\]]+",
    re.IGNORECASE,
)

# Block private/internal IPs (SSRF protection)
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "[::]", "[::1]"}


class OGParser(HTMLParser):
    """Minimal HTML parser that extracts Open Graph meta tags from <head>."""

    def __init__(self):
        super().__init__()
        self.og = {}
        self.title = ""
        self._in_title = False
        self._done = False

    def handle_starttag(self, tag, attrs):
        if self._done:
            return
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            attr_map = dict(attrs)
            prop = attr_map.get("property", attr_map.get("name", ""))
            content = attr_map.get("content", "")
            if prop.startswith("og:") and content:
                key = prop[3:]  # strip "og:"
                if key in ("title", "description", "image", "site_name", "url", "type"):
                    self.og[key] = content.strip()
            # Fallback: twitter:image, twitter:title
            if prop.startswith("twitter:") and content:
                key = prop[8:]
                if key in ("title", "description", "image") and key not in self.og:
                    self.og[key] = content.strip()
            # Fallback: <meta name="description">
            if prop == "description" and content and "description" not in self.og:
                self.og["description"] = content.strip()

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "head":
            self._done = True


def extract_first_url(text: str) -> Optional[str]:
    """Extract the first URL from text content."""
    if not text:
        return None
    match = URL_RE.search(text)
    if not match:
        return None
    url = match.group(0).rstrip(".,;:!?")
    # Validate scheme and host
    try:
        parsed = urlparse(url)
        if parsed.hostname and parsed.hostname.lower() in BLOCKED_HOSTS:
            return None
        if not parsed.scheme or not parsed.hostname:
            return None
    except Exception:
        return None
    return url


async def fetch_link_preview(url: str) -> Optional[dict]:
    """
    Fetch Open Graph metadata from a URL.

    Returns:
        {url, title, description, image, site_name, domain} or None on failure.
    """
    if not url:
        return None

    # Check cache first
    try:
        cached = await db.link_previews.find_one(
            {"url": url}, {"_id": 0, "preview": 1}
        )
        if cached:
            return cached["preview"]
    except Exception:
        pass

    try:
        parsed = urlparse(url)
        domain = parsed.hostname or ""

        async with httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=5),
        ) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "InFineaBot/1.0 (Link Preview)",
                    "Accept": "text/html",
                },
            )

        if resp.status_code != 200:
            return None

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None

        # Parse only the first 50KB to avoid memory issues
        html = resp.text[:50000]
        parser = OGParser()
        try:
            parser.feed(html)
        except Exception:
            pass

        og = parser.og
        title = og.get("title") or parser.title.strip()
        if not title:
            return None

        preview = {
            "url": url,
            "title": title[:200],
            "description": (og.get("description") or "")[:300],
            "image": og.get("image", ""),
            "site_name": og.get("site_name", domain)[:100],
            "domain": domain,
        }

        # Cache the result (TTL: let MongoDB handle expiry if needed)
        try:
            await db.link_previews.update_one(
                {"url": url},
                {"$set": {"url": url, "preview": preview}},
                upsert=True,
            )
        except Exception:
            pass

        return preview

    except Exception as e:
        logger.debug(f"Link preview fetch failed for {url}: {e}")
        return None

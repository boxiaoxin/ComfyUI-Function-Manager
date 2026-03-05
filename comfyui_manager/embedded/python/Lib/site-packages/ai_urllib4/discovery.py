"""
Discovery module for finding hidden APIs within HTML content.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

log = logging.getLogger(__name__)

class APIDiscoverer:
    """
    Analyzes HTML and JavaScript to find potential JSON API endpoints.
    """
    
    def __init__(self, ai_backend: Optional[Any] = None):
        self.ai_backend = ai_backend
        # Common API patterns
        self.url_patterns = [
            r'https?://[\w\.-]+/api/[\w\/\.-]+',
            r'/api/v[0-9]/[\w\/\.-]+',
            r'/graphql',
            r'/v[0-9]/[\w\/\.-]+',
            r'[\w\.-]+\.json',
            r'fetch\(["\'](.*?)["\']',
            r'axios\.(?:get|post)\(["\'](.*?)["\']',
            r'\.request\(["\'](.*?)["\']',
            r'url:\s*["\'](.*?)["\']',
            r'endpoint:\s*["\'](.*?)["\']',
        ]

    def find_potential_endpoints(self, html: str, base_url: str) -> List[str]:
        """
        Extract potential API URL candidates from HTML and JS.
        """
        candidates = set()
        
        # 1. Path transformation heuristics
        parsed = urlparse(base_url)
        path = parsed.path
        if not path.endswith(".json"):
             # Try adding .json to the path
             json_path = path.rstrip('/') + ".json"
             candidates.add(parsed._replace(path=json_path).geturl())
             
             # Try /api/ prefix (only if not already an API domain/path)
             if "api" not in parsed.netloc.lower() and "/api/" not in path.lower():
                 api_path = "/api" + path
                 candidates.add(parsed._replace(path=api_path).geturl())

        # 2. Look for patterns in the WHOLE HTML (not just scripts)
        # Some URLs are in data-attributes or plain strings
        for pattern in self.url_patterns:
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    for m in match:
                        if m: candidates.add(urljoin(base_url, m))
                else:
                    candidates.add(urljoin(base_url, match))

        # 3. Look for explicit JSON links or data attributes
        data_apis = re.findall(r'data-api=["\'](.*?)["\']', html)
        for api in data_apis:
            candidates.add(urljoin(base_url, api))
            
        # Filter for likely URLs
        filtered = {c for c in candidates if urlparse(c).scheme in ('http', 'https')}
            
        return list(filtered)

    def select_best_endpoint(self, url: str, candidates: List[str]) -> Optional[str]:
        """
        Use AI or heuristics to pick the most likely data-providing endpoint.
        """
        if not candidates:
            return None

        if self.ai_backend:
            prompt = (
                f"Given the original page URL: {url}\n"
                f"And these discovered potential API endpoints: {candidates[:10]}\n"
                "Which one is most likely the main JSON data API for this page? "
                "Return ONLY the URL string, or 'None' if unsure."
            )
            result = self.ai_backend.ask(prompt)
            if result and result.strip().lower() != "none" and result.strip() in candidates:
                return result.strip()

        # Heuristic fallback: Prefer longer URLs with 'api', 'v1', or 'json'
        scored = []
        for c in candidates:
            score = 0
            if "/api/" in c.lower(): score += 10
            if ".json" in c.lower(): score += 5
            if "graphql" in c.lower(): score += 8
            if "v1" in c.lower() or "v2" in c.lower(): score += 3
            scored.append((score, c))
            
        scored.sort(reverse=True)
        return scored[0][1] if scored else None

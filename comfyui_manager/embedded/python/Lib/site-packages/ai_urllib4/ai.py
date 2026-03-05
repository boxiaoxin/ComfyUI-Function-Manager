"""
AI-powered configuration advisor for ai-urllib4.

This module provides "intelligent" logic for request optimization,
response classification, and anomaly detection using local heuristics
and optional LLM-powered backends.
"""

from __future__ import annotations

import json
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)

class AIBackend(ABC):
    """Abstract base class for AI backends."""
    
    @abstractmethod
    def ask(self, prompt: str) -> Optional[str]:
        """Send a prompt to the AI and return the response."""
        pass

class GeminiBackend(AIBackend):
    """Backend for Google Gemini AI."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def ask(self, prompt: str) -> Optional[str]:
        import urllib.request
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            log.warning(f"Error querying Gemini: {e}")
            return None

class AIInsights:
    """Stores AI-driven insights for a domain."""
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.last_status = None
        self.avg_delay = 0.5  # Seconds
        self.total_requests = 0
        self.history: List[Dict[str, Any]] = []

class AISmartConfig:
    """AI-powered configuration advisor."""
    
    def __init__(self, backend: Optional[AIBackend] = None):
        self._insights: Dict[str, AIInsights] = {}
        self.backend = backend

    def _get_insights(self, domain_or_url: str) -> AIInsights:
        domain = urlparse(domain_or_url).netloc or domain_or_url
        if domain not in self._insights:
            self._insights[domain] = AIInsights()
        return self._insights[domain]

    def get_domain_insights(self, domain: str) -> Dict[str, Any]:
        i = self._get_insights(domain)
        return {
            "success_rate": i.success_count / max(1, i.total_requests),
            "avg_delay": i.avg_delay,
            "total_requests": i.total_requests
        }

    def classify_response(self, response: Any) -> str:
        """Classify a response as success, challenge, or block."""
        if 200 <= response.status < 300:
            return "success"
        
        body = (getattr(response, 'data', b"") or b"").lower()
        if response.status in (403, 429):
            if b"cloudflare" in body or b"captcha" in body or b"turnstile" in body:
                return "challenge"
            return "block"
        
        return "error"

    def learn_from_response(self, url: str, response: Any, elapsed: float):
        """Update domain insights based on response."""
        domain = urlparse(url).netloc or url
        i = self._get_insights(domain)
        i.total_requests += 1
        i.last_status = response.status
        
        classification = self.classify_response(response)
        if classification == "success":
            i.success_count += 1
            i.avg_delay = (i.avg_delay * 0.9) + (elapsed * 0.1)
        else:
            i.failure_count += 1
            i.avg_delay *= 1.2 # Slighly increase delay

        i.history.append({
            "status": response.status,
            "classification": classification,
            "elapsed": elapsed
        })
        if len(i.history) > 50: i.history.pop(0)

    def suggest_headers(self, url: str) -> Dict[str, str]:
        """Suggest optimal headers for a URL."""
        domain = urlparse(url).netloc or url
        i = self._get_insights(domain)

        headers = {
            "User-Agent": "ai-urllib4/2.1.0 (Smart)",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # If LLM is available and we're struggling, ask for help
        if self.backend and i.failure_count > 0:
            prompt = f"Optimize HTTP headers for {domain} following {i.failure_count} recent failures. Return ONLY a JSON dictionary."
            advice = self.backend.ask(prompt)
            if advice:
                try:
                    # Try to extract JSON from advice
                    start = advice.find("{")
                    end = advice.rfind("}") + 1
                    if start != -1 and end != -1:
                        new_headers = json.loads(advice[start:end])
                        headers.update(new_headers)
                except:
                    pass
            
        return headers

    def suggest_retry_strategy(self, url: str, response: Any) -> Dict[str, Any]:
        """Suggest a retry strategy based on the response."""
        classification = self.classify_response(response)
        
        if classification == "challenge":
            return {"retry": True, "delay": 5, "rotate_ua": True, "reason": "Bot challenge detected"}
        elif classification == "block":
            return {"retry": True, "delay": 10, "rotate_ua": True, "reason": "IP or UA block"}
            
        return {"retry": False}

    def detect_anomaly(self, response: Any) -> Dict[str, Any]:
        """Detect unusual response characteristics."""
        url = getattr(response, 'request_url', '')
        i = self._get_insights(url)
        
        is_anomaly = False
        reason = None
        
        if response.status >= 400:
            is_anomaly = True
            reason = f"High error status: {response.status}"
            
        return {"is_anomaly": is_anomaly, "reason": reason}

def optimize_params_for(url: str) -> Dict[str, Any]:
    """Returns a dict of optimized parameters for the given URL."""
    config = AISmartConfig()
    return {
        "headers": config.suggest_headers(url),
        "timeout": 30.0
    }

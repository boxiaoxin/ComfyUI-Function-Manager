"""
SmartClient - AI-enhanced PoolManager for ai-urllib4.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional

from .poolmanager import PoolManager
from .ai import AISmartConfig, optimize_params_for, GeminiBackend
from .discovery import APIDiscoverer
from .response import HTTPResponse
from .exceptions import AIInitializationError

log = logging.getLogger(__name__)

class SmartClient(PoolManager):
    """
    An AI-powered HTTP client that automatically optimizes requests,
    learns from responses, and provides domain-specific insights.
    """
    
    def __init__(
        self, 
        ai_optimize: bool = True, 
        learn_from_success: bool = True, 
        api_key: Optional[str] = None,
        ai_provider: str = "gemini",
        ai_model: str = "gemini-1.5-flash",
        **kwargs
    ):
        """
        Initialize a new SmartClient.
        
        :param ai_optimize: Whether to automatically optimize headers and timing.
        :param learn_from_success: Whether to learn from successful and failed requests.
        :param api_key: API key for the AI provider (e.g., Gemini).
        :param ai_provider: The AI provider to use ("gemini").
        :param ai_model: The AI model to use.
        :param kwargs: Arguments passed to PoolManager.
        """
        super().__init__(**kwargs)
        self.ai_optimize = ai_optimize
        self.learn_from_success = learn_from_success
        
        # Initialize AI backend
        self.ai_backend = None
        if api_key:
            if ai_provider == "gemini":
                try:
                    self.ai_backend = GeminiBackend(api_key, model=ai_model)
                except Exception as e:
                    raise AIInitializationError(f"Failed to initialize Gemini backend: {e}")
            else:
                raise AIInitializationError(f"Unsupported AI provider: {ai_provider}")
        
        try:
            self.ai_config = AISmartConfig(backend=self.ai_backend)
            self.discoverer = APIDiscoverer(ai_backend=self.ai_backend)
        except Exception as e:
            raise AIInitializationError(f"Failed to initialize AI components: {e}")

    def request(
        self, 
        method: str, 
        url: str, 
        **kw
    ) -> HTTPResponse:
        """
        Make an optimized request using AI heuristics and learned patterns.
        """
        if self.ai_optimize:
            # Get suggested headers
            ai_headers = self.ai_config.suggest_headers(url)
            
            # Merge AI suggested headers with user headers
            user_headers = kw.get("headers", {})
            headers = ai_headers.copy()
            headers.update(user_headers)
            kw["headers"] = headers
            
            # Default timeout
            if "timeout" not in kw:
                kw["timeout"] = 30.0

        start_time = time.time()
        attempt = 0

        while True:
            # Call the parent PoolManager request
            response = super().request(method, url, **kw)
            elapsed = time.time() - start_time
            
            # Learn from the response if enabled
            if self.learn_from_success:
                # Cache content to allow multiple reads for classification
                response.read(cache_content=True)
                self.ai_config.learn_from_response(url, response, elapsed)

            # AI Retry logic if optimized
            if self.ai_optimize and response.status >= 400:
                strategy = self.ai_config.suggest_retry_strategy(url, response)
                
                if strategy.get("retry") and attempt < 5:
                    log.info(f"AI suggesting retry for {url} (attempt {attempt+1}): {strategy.get('reason')}")
                    attempt += 1
                    time.sleep(strategy.get("delay", 1))
                    
                    if strategy.get("rotate_ua"):
                        kw["headers"]["User-Agent"] = f"ai-urllib4/2.1.0 (Retry-{attempt})"
                    
                    continue
            
            return response

    def get_domain_insights(self, domain: str) -> Dict[str, Any]:
        """
        Retrieve AI-driven insights for a specific domain.
        """
        return self.ai_config.get_domain_insights(domain)

    def detect_anomaly(self, response: HTTPResponse) -> Dict[str, Any]:
        """
        Analyze a response for potential anomalies or bot detection.
        """
        return self.ai_config.detect_anomaly(response)

    def discover_api(self, url: str, **kwargs) -> Optional[HTTPResponse]:
        """
        Attempt to automatically discover and fetch data from a hidden JSON API.
        """
        # 1. Fetch the original page
        log.info(f"Analyzing {url} for hidden APIs...")
        response = self.request("GET", url, **kwargs)
        
        if not response.data:
            return None

        # 2. Check if the original response is already JSON
        content_type = response.headers.get("Content-Type", "").lower()
        if "application/json" in content_type:
             log.info(f"Original URL {url} is already a JSON API.")
             setattr(response, "discovered_from", url)
             try:
                 setattr(response, "json_data", json.loads(response.data))
             except:
                 pass
             return response

        # 3. Extract potential endpoints
        html = response.data.decode(errors="ignore")
        candidates = self.discoverer.find_potential_endpoints(html, url)
        
        if not candidates:
            log.info("No API candidates found via heuristics.")
            return None

        # 3. Select the best one
        best_api = self.discoverer.select_best_endpoint(url, candidates)
        if not best_api:
            return None

        log.info(f"Discovered potential API: {best_api}")
        
        # 4. Fetch from the API
        api_response = self.request("GET", best_api, **kwargs)
        
        # 5. Check if it's actually JSON
        content_type = api_response.headers.get("Content-Type", "").lower()
        if "application/json" in content_type:
            log.info("Successfully matched JSON API!")
            # Add discovery metadata to the response
            setattr(api_response, "discovered_from", url)
            try:
                setattr(api_response, "json_data", json.loads(api_response.data))
            except:
                pass
            return api_response
            
        log.warning(f"Discovered URL {best_api} did not return valid JSON.")
        return None

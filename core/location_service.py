"""
Location detection service.
Uses external IP geolocation providers to infer the device location.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
import logging

import requests

logger = logging.getLogger(__name__)


class LocationService:
    """Best-effort current location detection using network geolocation."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.providers = (
            ("ipapi", "https://ipapi.co/json/"),
            ("ipwhois", "https://ipwho.is/"),
        )

    def detect_current_location(self) -> Optional[Dict[str, object]]:
        """Return normalized location data or None if all providers fail."""
        for provider_name, url in self.providers:
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                normalized = self._normalize(provider_name, data)
                if normalized:
                    logger.info(
                        "Detected current location using %s: %s, %s",
                        provider_name,
                        normalized.get("city", ""),
                        normalized.get("state", ""),
                    )
                    return normalized
            except Exception as exc:
                logger.warning("Location detection failed via %s: %s", provider_name, exc)

        logger.warning("Could not detect current location from available providers")
        return None

    def _normalize(self, provider_name: str, data: Dict[str, object]) -> Optional[Dict[str, object]]:
        """Normalize provider payloads into one shared shape."""
        if provider_name == "ipapi":
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            timezone = data.get("timezone")
            if latitude is None or longitude is None or not timezone:
                return None

            return {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "city": data.get("city", "") or "",
                "state": data.get("region_code", "") or data.get("region", "") or "",
                "country": data.get("country_name", "") or data.get("country", "") or "",
                "timezone": timezone,
                "location_source": "ip_geolocation",
                "location_provider": provider_name,
                "last_detected_at": datetime.now().isoformat(),
            }

        if provider_name == "ipwhois":
            success = bool(data.get("success", True))
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            timezone_data = data.get("timezone", {})
            timezone = timezone_data.get("id") if isinstance(timezone_data, dict) else None

            if not success or latitude is None or longitude is None or not timezone:
                return None

            return {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "city": data.get("city", "") or "",
                "state": data.get("region_code", "") or data.get("region", "") or "",
                "country": data.get("country", "") or "",
                "timezone": timezone,
                "location_source": "ip_geolocation",
                "location_provider": provider_name,
                "last_detected_at": datetime.now().isoformat(),
            }

        return None

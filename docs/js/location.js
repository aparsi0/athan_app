/**
 * Location detection — browser geolocation first, then IP-based fallback
 * (same providers as the desktop app: ipapi.co, ipwho.is).
 */
const LocationService = {
  async detect() {
    const fromBrowser = await this._fromBrowserGeolocation();
    if (fromBrowser) {
      // Enrich with a city name via reverse geocoding (best-effort).
      const named = await this._reverseGeocode(fromBrowser.latitude, fromBrowser.longitude);
      return { ...fromBrowser, ...named };
    }
    return this._fromIpProviders();
  },

  _fromBrowserGeolocation() {
    return new Promise((resolve) => {
      if (!('geolocation' in navigator)) return resolve(null);
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          location_source: 'browser_geolocation'
        }),
        () => resolve(null),
        { timeout: 8000, maximumAge: 600000 }
      );
    });
  },

  async _reverseGeocode(lat, lon) {
    try {
      const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`;
      const res = await fetchWithTimeout(url, 6000);
      if (!res.ok) return {};
      const data = await res.json();
      return {
        city: data.city || data.locality || '',
        state: data.principalSubdivisionCode?.split('-').pop() || data.principalSubdivision || '',
        country: data.countryName || ''
      };
    } catch {
      return {};
    }
  },

  async _fromIpProviders() {
    const providers = [
      { name: 'ipapi', url: 'https://ipapi.co/json/', parse: this._parseIpapi },
      { name: 'ipwhois', url: 'https://ipwho.is/', parse: this._parseIpwhois }
    ];
    for (const provider of providers) {
      try {
        const res = await fetchWithTimeout(provider.url, 6000);
        if (!res.ok) continue;
        const normalized = provider.parse(await res.json());
        if (normalized) return { ...normalized, location_provider: provider.name };
      } catch (e) {
        console.warn(`Location detection failed via ${provider.name}`, e);
      }
    }
    return null;
  },

  _parseIpapi(data) {
    if (data.latitude == null || data.longitude == null || !data.timezone) return null;
    return {
      latitude: Number(data.latitude),
      longitude: Number(data.longitude),
      city: data.city || '',
      state: data.region_code || data.region || '',
      country: data.country_name || data.country || '',
      timezone: data.timezone,
      location_source: 'ip_geolocation'
    };
  },

  _parseIpwhois(data) {
    const timezone = typeof data.timezone === 'object' ? data.timezone?.id : data.timezone;
    if (data.success === false || data.latitude == null || data.longitude == null || !timezone) return null;
    return {
      latitude: Number(data.latitude),
      longitude: Number(data.longitude),
      city: data.city || '',
      state: data.region_code || data.region || '',
      country: data.country || '',
      timezone,
      location_source: 'ip_geolocation'
    };
  }
};

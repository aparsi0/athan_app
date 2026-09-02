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

  /**
   * Turn coordinates into a place name — for DISPLAY ONLY. Prayer times are
   * computed from latitude/longitude and never from this label.
   *
   * The service can answer from the caller's IP instead of the coordinates it
   * was given. Safari users behind iCloud Private Relay saw "Helsinki, 18"
   * while Settings held the correct Raleigh coordinates: CoreLocation gave
   * the right position, but the request egressed from an Apple relay in
   * Finland and the answer came back describing that instead. ("18" is the
   * tail of FI-18, Uusimaa.) Two independent checks reject such an answer.
   */
  async _reverseGeocode(lat, lon) {
    try {
      const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`;
      const res = await fetchWithTimeout(url, 6000);
      if (!res.ok) return {};
      const data = await res.json();

      // 1. The response says so itself. When it cannot use the supplied
      //    coordinates it falls back to the caller's IP and reports
      //    lookupSource: "ip geolocation".
      if (typeof data.lookupSource === 'string' && /ip\s*geolocation/i.test(data.lookupSource)) {
        console.warn(`Reverse geocoding answered from our IP, not our coordinates (${data.city || data.principalSubdivision || 'unknown place'}) — keeping the existing label.`);
        return {};
      }

      // 2. Belt and braces: the response echoes the coordinates it actually
      //    used. If they contradict what we asked for by more than ~55 km,
      //    it is describing somewhere else.
      const gotLat = Number(data.latitude), gotLon = Number(data.longitude);
      if (Number.isFinite(gotLat) && Number.isFinite(gotLon)) {
        const drift = Math.max(Math.abs(gotLat - lat), Math.abs(gotLon - lon));
        if (drift > 0.5) {
          console.warn(`Reverse geocoding ignored our coordinates (asked ${lat.toFixed(4)}, ${lon.toFixed(4)} — answered ${gotLat.toFixed(4)}, ${gotLon.toFixed(4)}) — keeping the existing label.`);
          return {};
        }
      }

      // ISO 3166-2 tails make good abbreviations only when they are letters:
      // US-NC -> "NC", but FI-18 -> "18", which is meaningless to a reader.
      const isoTail = data.principalSubdivisionCode?.split('-').pop() || '';
      const state = /^[A-Za-z]+$/.test(isoTail) ? isoTail : (data.principalSubdivision || '');

      return {
        city: data.city || data.locality || '',
        state,
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

/**
 * Configuration management — mirrors the desktop app's config.json.
 * Persisted per-visitor in localStorage.
 */
const CONFIG_STORAGE_KEY = 'athan_web_config_v1';

const DEFAULT_CONFIG = {
  location: {
    auto_detect: true,
    latitude: 35.7796,
    longitude: -78.6382,
    city: 'Raleigh',
    state: 'NC',
    country: 'United States',
    timezone: 'America/New_York',
    location_source: 'default'
  },
  prayer_settings: {
    calculation_method: 2, // ISNA
    enabled_prayers: { fajr: true, dhuhr: true, asr: true, maghrib: true, isha: true }
  },
  audio_settings: {
    athan_volume: 0.8,
    audio_file: 'assets/audio/Azansoundtrack.m4a',
    athan_files: {
      fajr: 'assets/audio/fajr_athan.m4a',
      dhuhr: 'assets/audio/dhuhr_athan.m4a',
      asr: 'assets/audio/asr_athan.m4a',
      maghrib: 'assets/audio/maghrib_athan.m4a',
      isha: 'assets/audio/isha_athan.m4a'
    }
  },
  special_audio_settings: {
    friday_before_dhuhr: {
      enabled: true,
      reference_time: 'dhuhr',
      offset_minutes: 120,
      weekday: 4, // Python convention: Monday=0 … Friday=4
      audio_file: 'assets/audio/Surat_AlKahf.m4a',
      volume: 0.8
    },
    after_prayer_duaa: {
      enabled: true,
      audio_file: 'assets/audio/Duaa.m4a',
      volume: 0.8
    },
    pre_prayer_woduaa: {
      enabled: true,
      lead_minutes: 15,
      audio_file: 'assets/audio/Woduaa.m4a',
      volume: 0.65
    },
    morning_audio: {
      enabled: true,
      reference_time: 'dhuhr',
      offset_minutes: -240,
      audio_file: 'assets/audio/morning_audio.m4a',
      volume: 0.8
    },
    night_audio: {
      enabled: true,
      reference_time: 'asr',
      offset_minutes: 135,
      audio_file: 'assets/audio/night_audio.m4a',
      volume: 0.8
    }
  },
  ui_settings: {
    show_notifications: true
  }
};

function deepMerge(defaults, loaded) {
  const merged = Array.isArray(defaults) ? [...defaults] : { ...defaults };
  if (!loaded || typeof loaded !== 'object') return merged;
  for (const [key, value] of Object.entries(loaded)) {
    if (
      key in merged &&
      merged[key] && typeof merged[key] === 'object' && !Array.isArray(merged[key]) &&
      value && typeof value === 'object' && !Array.isArray(value)
    ) {
      merged[key] = deepMerge(merged[key], value);
    } else {
      merged[key] = value;
    }
  }
  return merged;
}

const Config = {
  data: null,

  load() {
    try {
      const raw = localStorage.getItem(CONFIG_STORAGE_KEY);
      this.data = raw ? deepMerge(DEFAULT_CONFIG, JSON.parse(raw)) : structuredClone(DEFAULT_CONFIG);
    } catch (e) {
      console.warn('Config load failed, using defaults', e);
      this.data = structuredClone(DEFAULT_CONFIG);
    }
    return this.data;
  },

  save() {
    try {
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(this.data));
    } catch (e) {
      console.warn('Config save failed', e);
    }
  },

  get(path, fallback = null) {
    let value = this.data;
    for (const key of path.split('.')) {
      if (value == null || typeof value !== 'object' || !(key in value)) return fallback;
      value = value[key];
    }
    return value;
  },

  set(path, value) {
    const keys = path.split('.');
    let target = this.data;
    for (const key of keys.slice(0, -1)) {
      if (typeof target[key] !== 'object' || target[key] === null) target[key] = {};
      target = target[key];
    }
    target[keys.at(-1)] = value;
    this.save();
  },

  reset() {
    this.data = structuredClone(DEFAULT_CONFIG);
    this.save();
  }
};

const CALCULATION_METHODS = {
  1: 'University of Islamic Sciences, Karachi',
  2: 'ISNA (Islamic Society of North America)',
  3: 'Muslim World League',
  4: 'Umm Al-Qura University, Makkah',
  5: 'Egyptian General Authority of Survey',
  7: 'Institute of Geophysics, University of Tehran',
  8: 'Gulf Region',
  9: 'Kuwait',
  10: 'Qatar',
  11: 'Majlis Ugama Islam Singapura',
  12: 'Union Organization islamic de France',
  13: 'Diyanet İşleri Başkanlığı, Turkey',
  14: 'Spiritual Administration of Muslims of Russia'
};

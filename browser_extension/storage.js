// Storage manager for extension settings and data

export class StorageManager {
  constructor() {
    this.settingsKey = 'bankPhishingGuardian_settings';
    this.analyticsKey = 'bankPhishingGuardian_analytics';
    this.cacheKey = 'bankPhishingGuardian_cache';
  }

  async getSettings() {
    try {
      const result = await chrome.storage.sync.get([this.settingsKey]);
      return result[this.settingsKey] || this.getDefaultSettings();
    } catch (error) {
      console.error('Failed to get settings:', error);
      return this.getDefaultSettings();
    }
  }

  async setSettings(settings) {
    try {
      await chrome.storage.sync.set({
        [this.settingsKey]: {
          ...this.getDefaultSettings(),
          ...settings,
          lastUpdated: Date.now()
        }
      });
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  }

  getDefaultSettings() {
    return {
      enabled: true,
      apiEndpoint: 'http://localhost:8000',
      autoAnalyze: true,
      showWarnings: true,
      sensitivity: 'medium',
      supportedProviders: ['gmail', 'outlook', 'yahoo'],
      notifications: true,
      collectAnalytics: true,
      theme: 'auto', // auto, light, dark
      position: 'top-right' // position of warning overlay
    };
  }

  async getAnalytics() {
    try {
      const result = await chrome.storage.local.get([this.analyticsKey]);
      return result[this.analyticsKey] || [];
    } catch (error) {
      console.error('Failed to get analytics:', error);
      return [];
    }
  }

  async addAnalyticsEntry(entry) {
    try {
      const analytics = await this.getAnalytics();
      analytics.push(entry);
      
      // Keep only last 1000 entries
      if (analytics.length > 1000) {
        analytics.splice(0, analytics.length - 1000);
      }
      
      await chrome.storage.local.set({
        [this.analyticsKey]: analytics
      });
      
      return true;
    } catch (error) {
      console.error('Failed to save analytics:', error);
      return false;
    }
  }

  async clearAnalytics() {
    try {
      await chrome.storage.local.remove([this.analyticsKey]);
      return true;
    } catch (error) {
      console.error('Failed to clear analytics:', error);
      return false;
    }
  }

  async getCache() {
    try {
      const result = await chrome.storage.local.get([this.cacheKey]);
      return result[this.cacheKey] || {};
    } catch (error) {
      console.error('Failed to get cache:', error);
      return {};
    }
  }

  async setCache(cache) {
    try {
      await chrome.storage.local.set({
        [this.cacheKey]: cache
      });
      return true;
    } catch (error) {
      console.error('Failed to save cache:', error);
      return false;
    }
  }

  async clearCache() {
    try {
      await chrome.storage.local.remove([this.cacheKey]);
      return true;
    } catch (error) {
      console.error('Failed to clear cache:', error);
      return false;
    }
  }

  // Listen for storage changes
  onSettingsChanged(callback) {
    chrome.storage.onChanged.addListener((changes, namespace) => {
      if (namespace === 'sync' && changes[this.settingsKey]) {
        callback(changes[this.settingsKey].newValue);
      }
    });
  }
}
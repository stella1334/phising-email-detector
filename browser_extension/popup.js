// Popup script for Bank Phishing Guardian

class PopupManager {
  constructor() {
    this.currentTab = null;
    this.settings = null;
    this.analytics = null;
    
    this.init();
  }

  async init() {
    // Get current tab
    this.currentTab = await this.getCurrentTab();
    
    // Load settings and data
    await this.loadData();
    
    // Setup UI
    this.setupEventListeners();
    this.updateUI();
    
    // Check API status
    await this.checkApiStatus();
    
    // Load current email analysis if available
    await this.loadCurrentEmailAnalysis();
  }

  async getCurrentTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  async loadData() {
    try {
      // Load settings
      const settingsResponse = await chrome.runtime.sendMessage({
        action: 'getSettings'
      });
      
      if (settingsResponse.success) {
        this.settings = settingsResponse.data;
      } else {
        this.settings = this.getDefaultSettings();
      }
      
      // Load analytics
      this.analytics = await this.getAnalytics();
      
    } catch (error) {
      console.error('Failed to load data:', error);
      this.settings = this.getDefaultSettings();
      this.analytics = [];
    }
  }

  getDefaultSettings() {
    return {
      enabled: true,
      apiEndpoint: 'http://localhost:8000',
      autoAnalyze: true,
      showWarnings: true,
      sensitivity: 'medium',
      notifications: true,
      collectAnalytics: true,
      theme: 'auto',
      position: 'top-right'
    };
  }

  async getAnalytics() {
    try {
      const result = await chrome.storage.local.get(['bankPhishingGuardian_analytics']);
      return result.bankPhishingGuardian_analytics || [];
    } catch (error) {
      console.error('Failed to get analytics:', error);
      return [];
    }
  }

  setupEventListeners() {
    // Enable/disable toggle
    document.getElementById('enabledToggle').addEventListener('change', (e) => {
      this.updateSetting('enabled', e.target.checked);
    });
    
    // Sensitivity selector
    document.getElementById('sensitivitySelect').addEventListener('change', (e) => {
      this.updateSetting('sensitivity', e.target.value);
    });
    
    // Action buttons
    document.getElementById('analyzeCurrentBtn').addEventListener('click', () => {
      this.analyzeCurrentEmail();
    });
    
    document.getElementById('viewDetailsBtn').addEventListener('click', () => {
      this.openDetailedView();
    });
    
    document.getElementById('settingsBtn').addEventListener('click', () => {
      this.openSettingsModal();
    });
    
    // Settings modal
    document.getElementById('closeSettingsModal').addEventListener('click', () => {
      this.closeSettingsModal();
    });
    
    document.getElementById('cancelSettingsBtn').addEventListener('click', () => {
      this.closeSettingsModal();
    });
    
    document.getElementById('saveSettingsBtn').addEventListener('click', () => {
      this.saveSettings();
    });
    
    document.getElementById('clearDataBtn').addEventListener('click', () => {
      this.clearAllData();
    });
    
    // Close modal on background click
    document.getElementById('settingsModal').addEventListener('click', (e) => {
      if (e.target.id === 'settingsModal') {
        this.closeSettingsModal();
      }
    });
  }

  updateUI() {
    // Update toggle states
    document.getElementById('enabledToggle').checked = this.settings.enabled;
    document.getElementById('sensitivitySelect').value = this.settings.sensitivity;
    
    // Update status
    this.updateStatus();
    
    // Update stats
    this.updateStats();
    
    // Update activity
    this.updateActivity();
  }

  updateStatus() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    
    if (this.settings.enabled) {
      statusDot.className = 'status-dot';
      statusText.textContent = 'Protection Active';
    } else {
      statusDot.className = 'status-dot error';
      statusText.textContent = 'Protection Disabled';
    }
  }

  updateStats() {
    const today = new Date().toDateString();
    const todayAnalytics = this.analytics.filter(entry => 
      new Date(entry.timestamp).toDateString() === today
    );
    
    const emailsAnalyzed = todayAnalytics.length;
    const threatsBlocked = todayAnalytics.filter(entry => entry.isPhishing).length;
    
    document.getElementById('emailsAnalyzed').textContent = emailsAnalyzed;
    document.getElementById('threatsBlocked').textContent = threatsBlocked;
  }

  updateActivity() {
    const activityList = document.getElementById('activityList');
    const recentActivities = this.analytics.slice(-5).reverse();
    
    if (recentActivities.length === 0) {
      activityList.innerHTML = `
        <div class="activity-item placeholder">
          <div class="activity-icon">📧</div>
          <div class="activity-content">
            <div class="activity-title">No recent activity</div>
            <div class="activity-time">Waiting for emails to analyze...</div>
          </div>
        </div>
      `;
      return;
    }
    
    activityList.innerHTML = recentActivities.map(activity => {
      const time = new Date(activity.timestamp).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      
      const icon = activity.isPhishing ? '🚨' : '✅';
      const title = activity.isPhishing ? 'Threat blocked' : 'Safe email';
      const provider = activity.provider ? ` (${activity.provider})` : '';
      
      return `
        <div class="activity-item">
          <div class="activity-icon">${icon}</div>
          <div class="activity-content">
            <div class="activity-title">${title}${provider}</div>
            <div class="activity-time">${time} - Risk: ${activity.riskScore}/100</div>
          </div>
        </div>
      `;
    }).join('');
  }

  async checkApiStatus() {
    const apiIndicator = document.getElementById('apiIndicator');
    const apiText = document.getElementById('apiText');
    
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'healthCheck'
      });
      
      if (response && response.success) {
        apiIndicator.textContent = '🟢';
        apiText.textContent = 'API Connected';
      } else {
        throw new Error(response?.error || 'Health check failed');
      }
    } catch (error) {
      console.error('API health check failed:', error);
      apiIndicator.textContent = '🔴';
      apiText.textContent = 'API server not responding';
    }
  }

  async loadCurrentEmailAnalysis() {
    // Check if we're on a supported email provider
    if (!this.isEmailProvider()) {
      return;
    }
    
    try {
      // Try to get current email analysis from content script
      const response = await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'getCurrentAnalysis'
      });
      
      if (response && response.analysis) {
        this.displayCurrentAnalysis(response.analysis);
      }
    } catch (error) {
      // Content script might not be ready or no current analysis
      console.log('No current analysis available');
    }
  }

  displayCurrentAnalysis(analysis) {
    const currentAnalysisSection = document.getElementById('currentAnalysis');
    currentAnalysisSection.style.display = 'block';
    
    const riskScore = analysis.risk_score || 0;
    const riskLevel = analysis.risk_level || 'safe';
    
    // Update score circle
    const scoreCircle = document.getElementById('riskScoreCircle');
    const scoreDegrees = (riskScore / 100) * 360;
    scoreCircle.style.setProperty('--score-deg', `${scoreDegrees}deg`);
    
    // Set circle color based on risk
    const colors = {
      safe: '#4caf50',
      warning: '#ff9800',
      danger: '#f44336',
      critical: '#d32f2f'
    };
    
    const color = colors[riskLevel] || colors.safe;
    scoreCircle.style.background = `conic-gradient(${color} 0deg, ${color} ${scoreDegrees}deg, #e9ecef ${scoreDegrees}deg 360deg)`;
    
    // Update text
    document.getElementById('riskScoreNumber').textContent = Math.round(riskScore);
    document.getElementById('riskLevel').textContent = riskLevel.toUpperCase();
    document.getElementById('riskLevel').className = `risk-level ${riskLevel}`;
    
    const descriptions = {
      safe: 'No threats detected',
      warning: 'Some suspicious elements',
      danger: 'High risk detected',
      critical: 'Critical threat detected'
    };
    
    document.getElementById('riskDescription').textContent = descriptions[riskLevel] || descriptions.safe;
  }

  async analyzeCurrentEmail() {
    if (!this.isEmailProvider()) {
      alert('Please navigate to an email provider (Gmail, Outlook, etc.) to analyze emails.');
      return;
    }
    
    try {
      const btn = document.getElementById('analyzeCurrentBtn');
      const originalText = btn.innerHTML;
      btn.innerHTML = '<span class="btn-icon">⏳</span>Analyzing...';
      btn.disabled = true;
      
      // First check if there's email content to analyze
      const emailInfoResponse = await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'getEmailInfo'
      });
      
      if (!emailInfoResponse?.success || !emailInfoResponse.data?.hasEmail) {
        throw new Error('No email content found. Please make sure you\'re viewing an email.');
      }
      
      console.log('Email info:', emailInfoResponse.data);
      
      // Send message to content script to analyze current email
      const response = await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'analyzeCurrentEmail'
      });
      
      if (response && response.success) {
        // Show success message
        btn.innerHTML = '<span class="btn-icon">✅</span>Analysis Started';
        
        // Refresh popup data after a delay to show results
        setTimeout(() => {
          this.loadStats();
          this.updateActivity();
        }, 2000);
        
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.disabled = false;
        }, 3000);
      } else {
        throw new Error(response?.error || 'Analysis failed');
      }
    } catch (error) {
      console.error('Email analysis failed:', error);
      
      // Show specific error messages
      let message = 'Analysis failed: ';
      if (error.message.includes('No email content')) {
        message += 'Please make sure you\'re viewing an email with content.';
      } else if (error.message.includes('Could not establish connection')) {
        message += 'Extension needs to be reloaded. Please refresh the page.';
      } else {
        message += error.message;
      }
      
      alert(message);
      
      // Reset button
      const btn = document.getElementById('analyzeCurrentBtn');
      btn.innerHTML = '<span class="btn-icon">🔍</span>Analyze Current Email';
      btn.disabled = false;
    }
  }

  isEmailProvider() {
    const hostname = this.currentTab.url;
    return hostname.includes('mail.google.com') ||
           hostname.includes('outlook.') ||
           hostname.includes('mail.yahoo.com') ||
           hostname.includes('mail.aol.com');
  }

  async updateSetting(key, value) {
    this.settings[key] = value;
    
    try {
      await chrome.runtime.sendMessage({
        action: 'updateSettings',
        settings: this.settings
      });
      
      this.updateStatus();
    } catch (error) {
      console.error('Failed to update setting:', error);
    }
  }

  openDetailedView() {
    // Open detailed analytics page
    chrome.tabs.create({
      url: chrome.runtime.getURL('detailed.html')
    });
  }

  openSettingsModal() {
    // Populate settings form
    document.getElementById('apiEndpointInput').value = this.settings.apiEndpoint;
    document.getElementById('autoAnalyzeInput').checked = this.settings.autoAnalyze;
    document.getElementById('showWarningsInput').checked = this.settings.showWarnings;
    document.getElementById('collectAnalyticsInput').checked = this.settings.collectAnalytics;
    document.getElementById('themeSelect').value = this.settings.theme;
    
    // Show modal
    document.getElementById('settingsModal').style.display = 'flex';
  }

  closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
  }

  async saveSettings() {
    // Get values from form
    const newSettings = {
      ...this.settings,
      apiEndpoint: document.getElementById('apiEndpointInput').value,
      autoAnalyze: document.getElementById('autoAnalyzeInput').checked,
      showWarnings: document.getElementById('showWarningsInput').checked,
      collectAnalytics: document.getElementById('collectAnalyticsInput').checked,
      theme: document.getElementById('themeSelect').value
    };
    
    try {
      await chrome.runtime.sendMessage({
        action: 'updateSettings',
        settings: newSettings
      });
      
      this.settings = newSettings;
      this.updateUI();
      this.closeSettingsModal();
      
      // Test new API endpoint
      await this.checkApiStatus();
      
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings. Please try again.');
    }
  }

  async clearAllData() {
    if (!confirm('Are you sure you want to clear all data? This cannot be undone.')) {
      return;
    }
    
    try {
      // Clear storage
      await chrome.storage.local.clear();
      await chrome.storage.sync.clear();
      
      // Reset to defaults
      this.settings = this.getDefaultSettings();
      this.analytics = [];
      
      // Update UI
      this.updateUI();
      this.closeSettingsModal();
      
      alert('All data cleared successfully.');
      
    } catch (error) {
      console.error('Failed to clear data:', error);
      alert('Failed to clear data. Please try again.');
    }
  }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new PopupManager();
});
// Background service worker for the Bank Phishing Guardian extension

import { PhishingAPI } from './api.js';
import { StorageManager } from './storage.js';

class BackgroundService {
  constructor() {
    this.api = new PhishingAPI();
    this.storage = new StorageManager();
    this.analysisCache = new Map();
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Handle installation
    chrome.runtime.onInstalled.addListener(this.handleInstall.bind(this));
    
    // Handle messages from content scripts
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
    
    // Handle extension icon click
    chrome.action.onClicked.addListener(this.handleIconClick.bind(this));
  }

  async handleInstall(details) {
    console.log('Bank Phishing Guardian installed:', details);
    
    // Set default settings
    await this.storage.setSettings({
      enabled: true,
      apiEndpoint: 'http://localhost:8000',
      autoAnalyze: true,
      showWarnings: true,
      sensitivity: 'medium', // low, medium, high
      supportedProviders: ['gmail', 'outlook', 'yahoo']
    });
    
    // Setup declarative content rules
    chrome.declarativeContent.onPageChanged.removeRules(undefined, () => {
      chrome.declarativeContent.onPageChanged.addRules([{
        conditions: [
          new chrome.declarativeContent.PageStateMatcher({
            pageUrl: { hostContains: 'mail.google.com' },
          }),
          new chrome.declarativeContent.PageStateMatcher({
            pageUrl: { hostContains: 'outlook.' },
          })
        ],
        actions: [new chrome.declarativeContent.ShowAction()]
      }]);
    });
  }

  async handleMessage(request, sender, sendResponse) {
    try {
      switch (request.action) {
        case 'analyzeEmail':
          const result = await this.analyzeEmail(request.emailData, sender.tab.id);
          sendResponse({ success: true, data: result });
          break;
          
        case 'getSettings':
          const settings = await this.storage.getSettings();
          sendResponse({ success: true, data: settings });
          break;
          
        case 'updateSettings':
          await this.storage.setSettings(request.settings);
          sendResponse({ success: true });
          break;
          
        case 'getCachedAnalysis':
          const cached = this.getCachedAnalysis(request.emailHash);
          sendResponse({ success: true, data: cached });
          break;
          
        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Background service error:', error);
      sendResponse({ success: false, error: error.message });
    }
    
    return true; // Keep message channel open for async response
  }

  async analyzeEmail(emailData, tabId) {
    try {
      // Generate email hash for caching
      const emailHash = await this.generateEmailHash(emailData);
      
      // Check cache first
      if (this.analysisCache.has(emailHash)) {
        console.log('Returning cached analysis for email');
        return this.analysisCache.get(emailHash);
      }
      
      // Get current settings
      const settings = await this.storage.getSettings();
      
      if (!settings.enabled) {
        return { enabled: false, message: 'Analysis disabled' };
      }
      
      // Prepare email for analysis
      const rawEmail = this.constructRawEmail(emailData);
      
      // Call API
      console.log('Analyzing email via API...');
      const analysis = await this.api.analyzeEmail({
        raw_email: rawEmail,
        sender_email: emailData.sender,
        subject: emailData.subject,
        additional_context: {
          provider: emailData.provider,
          timestamp: new Date().toISOString(),
          user_agent: navigator.userAgent
        }
      });
      
      // Process and cache result
      const processedResult = this.processAnalysisResult(analysis, settings);
      this.analysisCache.set(emailHash, processedResult);
      
      // Log analytics
      await this.logAnalytics(emailData, processedResult);
      
      return processedResult;
      
    } catch (error) {
      console.error('Email analysis failed:', error);
      return {
        error: true,
        message: 'Analysis failed: ' + error.message,
        fallback: true
      };
    }
  }

  constructRawEmail(emailData) {
    // Construct a basic email format for API
    let rawEmail = '';
    
    if (emailData.sender) rawEmail += `From: ${emailData.sender}\n`;
    if (emailData.recipient) rawEmail += `To: ${emailData.recipient}\n`;
    if (emailData.subject) rawEmail += `Subject: ${emailData.subject}\n`;
    if (emailData.date) rawEmail += `Date: ${emailData.date}\n`;
    if (emailData.messageId) rawEmail += `Message-ID: ${emailData.messageId}\n`;
    
    rawEmail += '\n'; // Header/body separator
    
    if (emailData.body) {
      rawEmail += emailData.body;
    }
    
    return rawEmail;
  }

  processAnalysisResult(analysis, settings) {
    // Apply user settings to analysis result
    const sensitivityThresholds = {
      low: { warning: 80, danger: 90 },
      medium: { warning: 60, danger: 80 },
      high: { warning: 40, danger: 60 }
    };
    
    const thresholds = sensitivityThresholds[settings.sensitivity] || sensitivityThresholds.medium;
    
    return {
      ...analysis,
      userSettings: {
        shouldShowWarning: analysis.risk_score >= thresholds.warning && settings.showWarnings,
        warningLevel: analysis.risk_score >= thresholds.danger ? 'danger' : 'warning',
        sensitivity: settings.sensitivity
      },
      processed: true,
      timestamp: Date.now()
    };
  }

  async generateEmailHash(emailData) {
    // Simple hash for caching (in production, use crypto.subtle)
    const content = JSON.stringify({
      sender: emailData.sender,
      subject: emailData.subject,
      bodyPreview: emailData.body?.substring(0, 200)
    });
    
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return hash.toString();
  }

  getCachedAnalysis(emailHash) {
    return this.analysisCache.get(emailHash) || null;
  }

  async logAnalytics(emailData, analysis) {
    // Log usage analytics (anonymized)
    try {
      const analytics = {
        timestamp: Date.now(),
        provider: emailData.provider,
        riskScore: analysis.risk_score,
        riskLevel: analysis.risk_level,
        isPhishing: analysis.is_phishing,
        processingTime: analysis.processing_time_ms
      };
      
      await this.storage.addAnalyticsEntry(analytics);
    } catch (error) {
      console.warn('Analytics logging failed:', error);
    }
  }

  handleIconClick(tab) {
    // Open popup or toggle analysis on current tab
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: () => {
        // Toggle extension visibility
        const event = new CustomEvent('bankPhishingGuardian:toggle');
        document.dispatchEvent(event);
      }
    });
  }
}

// Initialize background service
const backgroundService = new BackgroundService();

// Export for testing
if (typeof module !== 'undefined') {
  module.exports = { BackgroundService };
}
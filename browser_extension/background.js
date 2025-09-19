// Background service worker for the Bank Phishing Guardian extension

console.log('🚀 Background script starting...');

let backgroundService = null;

// Import modules with error handling
(async () => {
  try {
    console.log('📦 Importing modules...');
    const { PhishingAPI } = await import('./api.js');
    const { StorageManager } = await import('./storage.js');
    console.log('✅ Modules imported successfully');
    
    class BackgroundService {
      constructor() {
        console.log('🏗️ Initializing BackgroundService...');
        this.api = new PhishingAPI();
        this.storage = new StorageManager();
        this.analysisCache = new Map();
        this.setupEventListeners();
        console.log('✅ BackgroundService initialized successfully');
      }

  setupEventListeners() {
    console.log('🎧 Setting up event listeners...');
    
    // Handle installation
    chrome.runtime.onInstalled.addListener(this.handleInstall.bind(this));
    console.log('✅ onInstalled listener added');
    
    // Handle messages from content scripts
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
    console.log('✅ onMessage listener added');
    
    // Handle extension icon click
    chrome.action.onClicked.addListener(this.handleIconClick.bind(this));
    console.log('✅ onClicked listener added');
    
    console.log('🎧 All event listeners setup complete');
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

  handleMessage(request, sender, sendResponse) {
    console.log('📨 Background: Received message:', request);
    console.log('📨 Background: Sender:', sender);
    console.log('📨 Background: Message action:', request?.action);
    
    // Validate request structure
    if (!request || !request.action) {
      console.error('❌ Background: Invalid request format:', request);
      sendResponse({ success: false, error: 'Invalid request format' });
      return false;
    }

    console.log('🔄 Background: Processing message:', request.action);

    // Handle async operations properly
    (async () => {
      try {
        console.log('🔄 Background: Entering async handler for:', request.action);
        
        switch (request.action) {
          case 'analyzeEmail':
            console.log('📧 Background: Processing analyzeEmail request');
            if (!request.emailData) {
              console.error('❌ Background: No email data provided');
              sendResponse({ success: false, error: 'Email data is required' });
              return;
            }
            
            console.log('📧 Background: Email data received:', {
              sender: request.emailData.sender,
              subject: request.emailData.subject?.substring(0, 50),
              bodyLength: request.emailData.bodyText?.length
            });
            
            const result = await this.analyzeEmail(request.emailData, sender.tab?.id);
            console.log('📧 Background: Analysis result:', result);
            
            // Ensure result is properly structured
            if (result && !result.error) {
              console.log('✅ Background: Sending success response');
              sendResponse({ success: true, data: result });
            } else {
              console.log('❌ Background: Sending error response:', result);
              sendResponse({ 
                success: false, 
                error: result?.message || result?.error || 'Analysis failed' 
              });
            }
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
            
          case 'healthCheck':
            console.log('🏥 Background: Performing health check...');
            console.log('🏥 API base URL:', this.api.baseURL);
            try {
              const healthResult = await this.api.healthCheck();
              console.log('✅ Background: Health check successful:', healthResult);
              sendResponse({ success: true, data: healthResult });
            } catch (error) {
              console.error('❌ Background: Health check failed:', error);
              console.error('❌ Background: Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
              });
              sendResponse({ 
                success: false, 
                error: error.message || 'API server not responding' 
              });
            }
            break;
            
          default:
            console.log('❓ Background: Unknown action:', request.action);
            sendResponse({ success: false, error: 'Unknown action: ' + request.action });
        }
      } catch (error) {
        console.error('💥 Background service error:', error);
        console.error('💥 Background error stack:', error.stack);
        console.error('💥 Background error details:', {
          name: error.name,
          message: error.message,
          action: request.action
        });
        sendResponse({ 
          success: false, 
          error: error.message || 'Unexpected error occurred' 
        });
      }
    })();
    
    console.log('🔄 Background: Returning true to keep message channel open');
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
    console.log('🚀 Creating BackgroundService instance...');
    backgroundService = new BackgroundService();
    console.log('✅ Background service initialized successfully');
    
  } catch (error) {
    console.error('💥 Failed to initialize background service:', error);
    console.error('💥 Error stack:', error.stack);
    console.error('💥 This will prevent the extension from working properly');
    
    // Set up a minimal error handler so content scripts get some response
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      console.error('❌ Background service not available, request failed:', request);
      sendResponse({ 
        success: false, 
        error: 'Background service failed to initialize: ' + error.message 
      });
      return true;
    });
  }
})();

// Export for testing
if (typeof module !== 'undefined') {
  module.exports = { BackgroundService };
}
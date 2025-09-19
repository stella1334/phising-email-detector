// Content script for Bank Phishing Guardian
// Injects into email pages to analyze emails in real-time

class EmailExtractor {
  constructor() {
    this.provider = this.detectProvider();
    this.currentEmail = null;
    this.analysisOverlay = null;
    this.isAnalyzing = false;
    this.observers = [];
    
    this.init();
  }

  init() {
    console.log('Bank Phishing Guardian: Initializing on', this.provider);
    
    // Wait for page to load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    // Set up observers for email changes
    this.setupEmailObserver();
    
    // Listen for extension messages
    this.setupMessageListeners();
    
    // Initial analysis of current email
    setTimeout(() => this.analyzeCurrentEmail(), 2000);
  }

  detectProvider() {
    const hostname = window.location.hostname;
    
    if (hostname.includes('gmail') || hostname.includes('mail.google.com')) {
      return 'gmail';
    } else if (hostname.includes('outlook')) {
      return 'outlook';
    } else if (hostname.includes('yahoo')) {
      return 'yahoo';
    } else if (hostname.includes('aol')) {
      return 'aol';
    }
    
    return 'unknown';
  }

  setupEmailObserver() {
    // Different selectors for different providers
    const selectors = {
      gmail: {
        emailContainer: '[role="main"]',
        emailSubject: 'h2[data-thread-perm-id]',
        emailSender: '[email]',
        emailBody: '[dir="ltr"]',
        emailDate: '[title]'
      },
      outlook: {
        emailContainer: '[role="region"][aria-label*="message"]',
        emailSubject: '[role="heading"]',
        emailSender: '[data-testid="message-header-from"]',
        emailBody: '[data-testid="message-body"]',
        emailDate: '[data-testid="message-header-date"]'
      },
      yahoo: {
        emailContainer: '[data-test-id="message-view-container"]',
        emailSubject: '[data-test-id="message-subject"]',
        emailSender: '[data-test-id="message-from"]',
        emailBody: '[data-test-id="message-body"]',
        emailDate: '[data-test-id="message-date"]'
      }
    };

    const config = selectors[this.provider];
    if (!config) return;

    // Observe DOM changes
    const observer = new MutationObserver((mutations) => {
      let shouldAnalyze = false;
      
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          // Check if email content changed
          const emailContainer = document.querySelector(config.emailContainer);
          if (emailContainer && this.hasEmailChanged()) {
            shouldAnalyze = true;
          }
        }
      });
      
      if (shouldAnalyze) {
        this.debounceAnalysis();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    this.observers.push(observer);
  }

  hasEmailChanged() {
    const currentEmailData = this.extractEmailData();
    
    if (!this.currentEmail || !currentEmailData) {
      return true;
    }
    
    // Compare key fields
    return (
      this.currentEmail.subject !== currentEmailData.subject ||
      this.currentEmail.sender !== currentEmailData.sender ||
      this.currentEmail.body?.substring(0, 100) !== currentEmailData.body?.substring(0, 100)
    );
  }

  debounceAnalysis = this.debounce(() => {
    this.analyzeCurrentEmail();
  }, 1000);

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  async analyzeCurrentEmail() {
    if (this.isAnalyzing) return;
    
    try {
      this.isAnalyzing = true;
      
      const emailData = this.extractEmailData();
      if (!emailData || !emailData.body) {
        return;
      }
      
      this.currentEmail = emailData;
      
      // Show loading indicator
      this.showAnalysisIndicator('analyzing');
      
      // Send to background script for analysis
      const response = await chrome.runtime.sendMessage({
        action: 'analyzeEmail',
        emailData: emailData
      });
      
      if (response.success) {
        this.displayAnalysisResult(response.data);
      } else {
        this.showAnalysisIndicator('error', response.error);
      }
      
    } catch (error) {
      console.error('Email analysis failed:', error);
      this.showAnalysisIndicator('error', error.message);
    } finally {
      this.isAnalyzing = false;
    }
  }

  extractEmailData() {
    try {
      const selectors = this.getSelectors();
      if (!selectors) return null;
      
      const emailData = {
        provider: this.provider,
        url: window.location.href,
        timestamp: new Date().toISOString()
      };
      
      // Extract subject
      const subjectElement = document.querySelector(selectors.emailSubject);
      emailData.subject = subjectElement?.textContent?.trim() || '';
      
      // Extract sender
      const senderElement = document.querySelector(selectors.emailSender);
      emailData.sender = this.extractEmailAddress(senderElement);
      
      // Extract date
      const dateElement = document.querySelector(selectors.emailDate);
      emailData.date = dateElement?.getAttribute('title') || dateElement?.textContent?.trim();
      
      // Extract body
      const bodyElement = document.querySelector(selectors.emailBody);
      if (bodyElement) {
        emailData.body = bodyElement.innerHTML || bodyElement.textContent;
        emailData.bodyText = bodyElement.textContent?.trim();
      }
      
      // Extract links
      emailData.links = this.extractLinks(bodyElement);
      
      // Extract recipient (current user)
      emailData.recipient = this.extractRecipient();
      
      return emailData;
      
    } catch (error) {
      console.error('Email extraction failed:', error);
      return null;
    }
  }

  getSelectors() {
    const selectors = {
      gmail: {
        emailSubject: 'h2[data-thread-perm-id], .hP',
        emailSender: '[email], .go span[email]',
        emailBody: '[dir="ltr"], .ii.gt div',
        emailDate: '.g3 span[title]'
      },
      outlook: {
        emailSubject: '[data-testid="message-subject"], [aria-label*="Subject"]',
        emailSender: '[data-testid="message-header-from"] button',
        emailBody: '[data-testid="message-body"], .elementToProof',
        emailDate: '[data-testid="message-header-date"]'
      },
      yahoo: {
        emailSubject: '[data-test-id="message-subject"]',
        emailSender: '[data-test-id="message-from"]',
        emailBody: '[data-test-id="message-body"]',
        emailDate: '[data-test-id="message-date"]'
      }
    };
    
    return selectors[this.provider];
  }

  extractEmailAddress(element) {
    if (!element) return '';
    
    // Try to get email from various attributes
    const emailAttr = element.getAttribute('email') || 
                     element.getAttribute('data-email') ||
                     element.getAttribute('title');
    
    if (emailAttr) return emailAttr;
    
    // Extract from text content
    const text = element.textContent || '';
    const emailMatch = text.match(/[\w\.-]+@[\w\.-]+\.[\w]+/);
    return emailMatch ? emailMatch[0] : text.trim();
  }

  extractLinks(bodyElement) {
    if (!bodyElement) return [];
    
    const links = [];
    const linkElements = bodyElement.querySelectorAll('a[href]');
    
    linkElements.forEach(link => {
      const href = link.getAttribute('href');
      if (href && href.startsWith('http')) {
        links.push({
          url: href,
          text: link.textContent?.trim(),
          title: link.getAttribute('title')
        });
      }
    });
    
    return links;
  }

  extractRecipient() {
    // Try to get current user's email
    const userEmail = document.querySelector('[data-hovercard-id]')?.getAttribute('data-hovercard-id') ||
                     document.querySelector('[title*="@"]')?.getAttribute('title');
    
    return userEmail || '';
  }

  displayAnalysisResult(analysis) {
    // Remove existing overlay
    this.removeAnalysisOverlay();
    
    if (!analysis.userSettings?.shouldShowWarning) {
      // Show green check for safe emails
      this.showAnalysisIndicator('safe', 'Email appears safe');
      return;
    }
    
    // Create warning overlay
    this.createWarningOverlay(analysis);
  }

  createWarningOverlay(analysis) {
    const overlay = document.createElement('div');
    overlay.className = 'bpg-warning-overlay';
    overlay.setAttribute('data-bpg-overlay', 'true');
    
    const warningLevel = analysis.userSettings.warningLevel;
    const riskScore = analysis.risk_score;
    
    overlay.innerHTML = `
      <div class="bpg-warning-content ${warningLevel}">
        <div class="bpg-warning-header">
          <div class="bpg-warning-icon">
            ${warningLevel === 'danger' ? '🚨' : '⚠️'}
          </div>
          <div class="bpg-warning-title">
            ${warningLevel === 'danger' ? 'HIGH RISK EMAIL' : 'SUSPICIOUS EMAIL'}
          </div>
          <div class="bpg-warning-score">
            Risk: ${riskScore}/100
          </div>
          <button class="bpg-close-btn" onclick="this.closest('.bpg-warning-overlay').remove()">
            ×
          </button>
        </div>
        
        <div class="bpg-warning-body">
          <div class="bpg-concerns">
            <strong>Key Concerns:</strong>
            <ul>
              ${analysis.gemini_analysis.key_concerns.map(concern => 
                `<li>${this.escapeHtml(concern)}</li>`
              ).join('')}
            </ul>
          </div>
          
          <div class="bpg-indicators">
            <strong>Suspicious Indicators:</strong>
            <div class="bpg-indicator-list">
              ${analysis.suspicious_indicators.slice(0, 5).map(indicator => `
                <div class="bpg-indicator">
                  <span class="bpg-indicator-type">${indicator.type.toUpperCase()}</span>
                  <span class="bpg-indicator-reason">${this.escapeHtml(indicator.reason)}</span>
                </div>
              `).join('')}
            </div>
          </div>
          
          <div class="bpg-actions">
            <button class="bpg-btn bpg-btn-danger" onclick="window.bpgExtension.reportPhishing()">
              Report as Phishing
            </button>
            <button class="bpg-btn bpg-btn-secondary" onclick="window.bpgExtension.markSafe()">
              Mark as Safe
            </button>
            <button class="bpg-btn bpg-btn-info" onclick="window.bpgExtension.showDetails()">
              View Details
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    this.analysisOverlay = overlay;
    
    // Auto-hide after 30 seconds for warning level
    if (warningLevel === 'warning') {
      setTimeout(() => {
        if (overlay.parentNode) {
          overlay.remove();
        }
      }, 30000);
    }
  }

  showAnalysisIndicator(status, message = '') {
    // Remove existing indicator
    const existing = document.querySelector('.bpg-indicator-badge');
    if (existing) existing.remove();
    
    const indicator = document.createElement('div');
    indicator.className = 'bpg-indicator-badge';
    indicator.setAttribute('data-status', status);
    
    const icons = {
      analyzing: '🔍',
      safe: '✅',
      warning: '⚠️',
      danger: '🚨',
      error: '❌'
    };
    
    const messages = {
      analyzing: 'Analyzing email...',
      safe: 'Email appears safe',
      warning: 'Suspicious email detected',
      danger: 'High risk email detected',
      error: message || 'Analysis failed'
    };
    
    indicator.innerHTML = `
      <div class="bpg-indicator-content">
        <span class="bpg-indicator-icon">${icons[status] || '?'}</span>
        <span class="bpg-indicator-text">${messages[status]}</span>
      </div>
    `;
    
    document.body.appendChild(indicator);
    
    // Auto-remove after delay for certain statuses
    if (['analyzing', 'safe'].includes(status)) {
      setTimeout(() => {
        if (indicator.parentNode) {
          indicator.remove();
        }
      }, status === 'analyzing' ? 10000 : 5000);
    }
  }

  removeAnalysisOverlay() {
    const overlays = document.querySelectorAll('[data-bpg-overlay]');
    overlays.forEach(overlay => overlay.remove());
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  setupMessageListeners() {
    // Listen for extension toggle
    document.addEventListener('bankPhishingGuardian:toggle', () => {
      if (this.analysisOverlay) {
        this.removeAnalysisOverlay();
      } else {
        this.analyzeCurrentEmail();
      }
    });
    
    // Expose extension API for overlay buttons
    window.bpgExtension = {
      reportPhishing: () => this.reportPhishing(),
      markSafe: () => this.markSafe(),
      showDetails: () => this.showDetails()
    };
  }

  async reportPhishing() {
    // Implementation for reporting phishing
    alert('Phishing report sent! Thank you for helping improve our detection.');
    this.removeAnalysisOverlay();
  }

  async markSafe() {
    // Implementation for marking as safe
    this.removeAnalysisOverlay();
    this.showAnalysisIndicator('safe', 'Marked as safe');
  }

  showDetails() {
    // Implementation for showing detailed analysis
    chrome.runtime.sendMessage({
      action: 'openDetailedView',
      emailData: this.currentEmail
    });
  }

  cleanup() {
    // Clean up observers and overlays
    this.observers.forEach(observer => observer.disconnect());
    this.removeAnalysisOverlay();
  }
}

// Initialize the email extractor
const emailExtractor = new EmailExtractor();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  emailExtractor.cleanup();
});

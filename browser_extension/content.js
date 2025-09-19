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
      if (!emailData || !emailData.bodyText || emailData.bodyText.length < 10) {
        console.warn('No valid email content found for analysis');
        this.showAnalysisIndicator('error', 'Failed to analyze email. Please make sure you\'re viewing an email.');
        return;
      }
      
      this.currentEmail = emailData;
      
      // Show loading indicator
      this.showAnalysisIndicator('analyzing');
      
      // Send to background script for analysis
      console.log('📤 Content: Sending message to background script:', {
        action: 'analyzeEmail',
        sender: emailData.sender,
        subject: emailData.subject?.substring(0, 50)
      });
      
<<<<<<< HEAD
      // Better error handling for undefined responses
      if (!response) {
        throw new Error('No response received from background script');
      }
      
=======
      const response = await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Background script response timeout (10s)'));
        }, 10000);
        
        chrome.runtime.sendMessage({
          action: 'analyzeEmail',
          emailData: emailData
        }, (response) => {
          clearTimeout(timeout);
          if (chrome.runtime.lastError) {
            console.error('📥 Content: Chrome runtime error:', chrome.runtime.lastError);
            reject(new Error('Chrome runtime error: ' + chrome.runtime.lastError.message));
          } else {
            console.log('📥 Content: Received response from background:', response);
            resolve(response);
          }
        });
      });
      
      // Better error handling for undefined responses
      if (!response) {
        console.error('📥 Content: No response received from background script');
        throw new Error('No response received from background script');
      }
      
      console.log('📥 Content: Response received:', {
        success: response.success,
        hasData: !!response.data,
        error: response.error
      });
      
>>>>>>> da8d9a8d2576a4b99ea8262079eff67765b40a07
      if (response.success === true && response.data) {
        this.displayAnalysisResult(response.data);
      } else if (response.success === false) {
        this.showAnalysisIndicator('error', response.error || 'Analysis failed');
      } else {
        // Handle malformed response
        console.error('Malformed response:', response);
        this.showAnalysisIndicator('error', 'Received invalid response from server');
      }
      
    } catch (error) {
      console.error('Email analysis failed:', error);
      
      // More specific error messages
      let errorMessage = 'Analysis failed';
      if (error.message.includes('Extension context invalidated')) {
        errorMessage = 'Extension needs to be reloaded';
      } else if (error.message.includes('network')) {
        errorMessage = 'Network connection failed';
      } else if (error.message.includes('No response')) {
        errorMessage = 'API server not responding';
      } else {
        errorMessage = error.message || 'Unknown error occurred';
      }
      
      this.showAnalysisIndicator('error', errorMessage);
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
      
      console.log('Extracting email data for:', this.provider);
      
      // Extract subject with multiple fallbacks
      const subjectSelectors = selectors.emailSubject.split(', ');
      for (const selector of subjectSelectors) {
        const element = document.querySelector(selector.trim());
        if (element && element.textContent?.trim()) {
          emailData.subject = element.textContent.trim();
          console.log('Found subject:', emailData.subject);
          break;
        }
      }
      
      // Extract sender with multiple fallbacks
      const senderSelectors = selectors.emailSender.split(', ');
      for (const selector of senderSelectors) {
        const element = document.querySelector(selector.trim());
        if (element) {
          const extractedSender = this.extractEmailAddress(element);
          if (extractedSender) {
            emailData.sender = extractedSender;
            console.log('Found sender:', emailData.sender);
            break;
          }
        }
      }
      
      // Extract date with multiple fallbacks
      const dateSelectors = selectors.emailDate.split(', ');
      for (const selector of dateSelectors) {
        const element = document.querySelector(selector.trim());
        if (element) {
          emailData.date = element.getAttribute('title') || element.textContent?.trim();
          if (emailData.date) {
            console.log('Found date:', emailData.date);
            break;
          }
        }
      }
      
      // Extract body with multiple fallbacks
      const bodySelectors = selectors.emailBody.split(', ');
      for (const selector of bodySelectors) {
        const element = document.querySelector(selector.trim());
        if (element && element.textContent?.trim()) {
          emailData.body = element.innerHTML || element.textContent;
          emailData.bodyText = element.textContent?.trim();
          console.log('Found body text length:', emailData.bodyText?.length || 0);
          break;
        }
      }
      
      // Fallback: try to find any email content on the page
      if (!emailData.bodyText || emailData.bodyText.length < 10) {
        // Try broader selectors for Gmail
        const fallbackSelectors = [
          '.nH .if .h7', // Gmail message body
          '.ii.gt', // Gmail message container
          '[role="main"] div[dir="ltr"]', // Gmail main content
          '[role="listitem"] div[dir="ltr"]', // Gmail message in list
          '.adn.ads div', // Gmail conversation
        ];
        
        for (const selector of fallbackSelectors) {
          const elements = document.querySelectorAll(selector);
          for (const element of elements) {
            const text = element.textContent?.trim();
            if (text && text.length > 20) {
              emailData.body = element.innerHTML || element.textContent;
              emailData.bodyText = text;
              console.log('Found body text via fallback:', text.substring(0, 100));
              break;
            }
          }
          if (emailData.bodyText && emailData.bodyText.length > 20) break;
        }
      }
      
      // Extract links
      emailData.links = this.extractLinks(document);
      
      // Extract recipient (current user)
      emailData.recipient = this.extractRecipient();
      
      // Validate we have minimum required data
      if (!emailData.bodyText || emailData.bodyText.length < 10) {
        console.warn('Insufficient email content found');
        return null;
      }
      
      console.log('Successfully extracted email data:', {
        subject: emailData.subject?.substring(0, 50) || 'No subject',
        sender: emailData.sender || 'No sender',
        bodyLength: emailData.bodyText?.length || 0,
        linksCount: emailData.links?.length || 0
      });
      
      return emailData;
      
    } catch (error) {
      console.error('Email extraction failed:', error);
      return null;
    }
  }

  getSelectors() {
    const selectors = {
      gmail: {
        // Updated selectors for current Gmail interface (2025)
        emailSubject: 'h2[data-thread-perm-id], .hP, [data-testid="thread-subject"], [role="heading"]',
        emailSender: '[email], .go span[email], [data-testid="sender-info"] span, .gb_Va .gb_lb, [data-hovercard-id*="@"], .gs .gD, span[email], .qu .go .gD',
        emailBody: '.ii.gt div, [data-testid="message-body"], .a3s.aiL, [dir="ltr"][class*="ii"], .AO .y6 .a3s, .nH .if .h7',
        emailDate: '.g3 span[title], [data-testid="message-date"], .g3 .gH .gK, span[title*=":"], .nH .g3 span',
        emailContainer: '[role="main"], .nH .if, .Bs .nH'
      },
      outlook: {
        emailSubject: '[data-testid="message-subject"], [aria-label*="Subject"], [role="heading"]',
        emailSender: '[data-testid="message-header-from"] button, [data-testid="sender-info"]',
        emailBody: '[data-testid="message-body"], .elementToProof, [role="document"]',
        emailDate: '[data-testid="message-header-date"]',
        emailContainer: '[role="region"][aria-label*="message"]'
      },
      yahoo: {
        emailSubject: '[data-test-id="message-subject"]',
        emailSender: '[data-test-id="message-from"]', 
        emailBody: '[data-test-id="message-body"]',
        emailDate: '[data-test-id="message-date"]',
        emailContainer: '[data-test-id="message-view-container"]'
      }
    };
    
    return selectors[this.provider];
  }

  extractEmailAddress(element) {
    if (!element) return '';
    
    // Try to get email from various attributes
    const emailAttr = element.getAttribute('email') || 
                     element.getAttribute('data-email') ||
                     element.getAttribute('data-hovercard-id') ||
                     element.getAttribute('title');
    
    if (emailAttr && emailAttr.includes('@')) return emailAttr;
    
    // Look for email in child elements
    const emailChild = element.querySelector('[email], [data-hovercard-id*="@"], span[email]');
    if (emailChild) {
      const childEmail = emailChild.getAttribute('email') || 
                        emailChild.getAttribute('data-hovercard-id') ||
                        emailChild.textContent;
      if (childEmail && childEmail.includes('@')) return childEmail;
    }
    
    // Extract from text content
    const text = element.textContent || '';
    const emailMatch = text.match(/[\w\.-]+@[\w\.-]+\.[\w]+/);
    if (emailMatch) return emailMatch[0];
    
    // If no email found, try to find it in nearby elements for Gmail
    if (this.provider === 'gmail') {
      // Look for sender info in Gmail's structure
      const gmailSenderSelectors = [
        '.go .gD[email]',
        '.gD[email]',
        '[data-hovercard-id*="@"]',
        '.qu .go .gD',
        '.go span[email]'
      ];
      
      for (const selector of gmailSenderSelectors) {
        const senderEl = document.querySelector(selector);
        if (senderEl) {
          const email = senderEl.getAttribute('email') || 
                       senderEl.getAttribute('data-hovercard-id') ||
                       senderEl.textContent;
          if (email && email.includes('@')) {
            return email;
          }
        }
      }
    }
    
    return text.trim();
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
    
    // Listen for manual analysis requests from popup
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (request.action === 'analyzeCurrentEmail') {
        this.analyzeCurrentEmail()
          .then(() => {
            sendResponse({ success: true, message: 'Analysis started' });
          })
          .catch(error => {
            sendResponse({ success: false, error: error.message });
          });
        return true; // Indicates async response
      }
      
      if (request.action === 'getEmailInfo') {
        const emailData = this.extractEmailData();
        sendResponse({ 
          success: true, 
          data: {
            hasEmail: !!emailData && !!emailData.bodyText,
            subject: emailData?.subject?.substring(0, 50) || 'No subject',
            sender: emailData?.sender || 'No sender',
            bodyLength: emailData?.bodyText?.length || 0
          }
        });
        return false; // Sync response
      }
    });
    
    // Expose extension API for overlay buttons
    window.bpgExtension = {
      reportPhishing: () => this.reportPhishing(),
      markSafe: () => this.markSafe(),
      showDetails: () => this.showDetails(),
      analyzeCurrentEmail: () => this.analyzeCurrentEmail(),
      extractEmailData: () => this.extractEmailData()
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
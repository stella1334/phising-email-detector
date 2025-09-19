// Debug utilities for the Bank Phishing Guardian extension
// Add this to content.js for testing or create a separate debug script

class ExtensionDebugger {
  constructor() {
    this.testMode = true;
  }

  // Test email extraction on current Gmail page
  testEmailExtraction() {
    console.log('=== EMAIL EXTRACTION TEST ===');
    
    // Test current Gmail structure
    const testSelectors = [
      {
        name: 'Subject',
        selectors: [
          'h2[data-thread-perm-id]',
          '.hP',
          '[data-testid="thread-subject"]',
          '[role="heading"]'
        ]
      },
      {
        name: 'Sender',
        selectors: [
          '[email]',
          '.go span[email]',
          '[data-hovercard-id*="@"]',
          '.gs .gD',
          'span[email]',
          '.qu .go .gD'
        ]
      },
      {
        name: 'Body',
        selectors: [
          '.ii.gt div',
          '.a3s.aiL',
          '[dir="ltr"][class*="ii"]',
          '.AO .y6 .a3s',
          '.nH .if .h7'
        ]
      }
    ];

    testSelectors.forEach(test => {
      console.log(`\n--- Testing ${test.name} selectors ---`);
      test.selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`${selector}: ${elements.length} elements found`);
        
        if (elements.length > 0) {
          const firstElement = elements[0];
          const text = firstElement.textContent?.trim();
          console.log(`  First element text: "${text?.substring(0, 100)}${text?.length > 100 ? '...' : ''}"`);
          console.log(`  Element attributes:`, [...firstElement.attributes].map(attr => `${attr.name}="${attr.value}"`));
        }
      });
    });

    // Test current page structure
    console.log('\n--- Current Page Analysis ---');
    console.log('URL:', window.location.href);
    console.log('Main role elements:', document.querySelectorAll('[role="main"]').length);
    console.log('Gmail-specific elements:', document.querySelectorAll('.nH').length);
    console.log('Message elements:', document.querySelectorAll('.ii').length);
    
    return true;
  }

  // Test API connectivity
  async testAPIConnection() {
    console.log('=== API CONNECTION TEST ===');
    
    try {
      // Test via extension background script (proper way for Chrome extensions)
      const response = await chrome.runtime.sendMessage({
        action: 'healthCheck'
      });
      
      if (response && response.success) {
        console.log('✅ API server is running:', response.data);
        return true;
      } else {
        console.log('❌ API server returned error:', response?.error || 'Unknown error');
        return false;
      }
    } catch (error) {
      console.log('❌ API server connection failed:', error.message);
      console.log('Note: This might be normal if run outside of the extension context');
      
      // Fallback to direct fetch for debugging outside extension context
      try {
        const directResponse = await fetch('http://localhost:8000/health');
        if (directResponse.ok) {
          const data = await directResponse.json();
          console.log('✅ Direct API test successful:', data);
          console.log('⚠️  But extension should use message passing for API calls');
          return true;
        }
      } catch (directError) {
        console.log('❌ Direct API test also failed:', directError.message);
      }
      
      return false;
    }
  }

  // Test extension messaging
  async testExtensionMessaging() {
    console.log('=== EXTENSION MESSAGING TEST ===');
    
    try {
      const response = await chrome.runtime.sendMessage({
        action: 'getSettings'
      });
      
      console.log('✅ Extension messaging works:', response);
      return true;
    } catch (error) {
      console.log('❌ Extension messaging failed:', error.message);
      return false;
    }
  }

  // Run all tests
  async runAllTests() {
    console.log('🚀 Starting Bank Phishing Guardian Debug Tests...\n');
    
    const results = {
      emailExtraction: this.testEmailExtraction(),
      apiConnection: await this.testAPIConnection(),
      extensionMessaging: await this.testExtensionMessaging()
    };
    
    console.log('\n=== TEST RESULTS SUMMARY ===');
    Object.entries(results).forEach(([test, result]) => {
      console.log(`${result ? '✅' : '❌'} ${test}: ${result ? 'PASS' : 'FAIL'}`);
    });
    
    return results;
  }
}

// Auto-run debug tests if in Gmail and debug mode is enabled
if (window.location.hostname.includes('gmail') && 
    (localStorage.getItem('phishing-debug') === 'true' || 
     new URLSearchParams(window.location.search).get('debug') === 'true')) {
  
  setTimeout(() => {
    const debugger = new ExtensionDebugger();
    debugger.runAllTests();
  }, 3000);
}

// Make debugger globally available
window.PhishingDebugger = ExtensionDebugger;

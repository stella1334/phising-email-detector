// API client for communicating with the Bank Phishing Detector service

export class PhishingAPI {
  constructor() {
    this.baseURL = 'http://localhost:8000'; // Default local development
    this.timeout = 30000; // 30 second timeout
    this.retryAttempts = 3;
  }

  async setBaseURL(url) {
    this.baseURL = url;
    
    // Test connectivity
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      console.error('API connectivity test failed:', error);
      return false;
    }
  }

  async healthCheck() {
    const response = await this.makeRequest('GET', '/health');
    return response;
  }

  async analyzeEmail(emailData) {
    const response = await this.makeRequest('POST', '/analyze', emailData);
    return response;
  }

  async analyzeBulkEmails(emails) {
    const response = await this.makeRequest('POST', '/analyze/bulk', { emails });
    return response;
  }

  async getStatus() {
    const response = await this.makeRequest('GET', '/status');
    return response;
  }

  async makeRequest(method, endpoint, data = null, attempt = 1) {
    try {
      const url = this.baseURL + endpoint;
      
      const options = {
        method,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'BankPhishingGuardian-Extension/1.0.0'
        },
        signal: AbortSignal.timeout(this.timeout)
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      return result;
      
    } catch (error) {
      console.error(`API request failed (attempt ${attempt}):`, error);
      
      // Retry logic
      if (attempt < this.retryAttempts && this.shouldRetry(error)) {
        console.log(`Retrying request in ${attempt * 1000}ms...`);
        await this.delay(attempt * 1000);
        return this.makeRequest(method, endpoint, data, attempt + 1);
      }
      
      throw error;
    }
  }

  shouldRetry(error) {
    // Retry on network errors but not on client errors (4xx)
    return (
      error.name === 'TypeError' || // Network error
      error.name === 'AbortError' || // Timeout
      (error.message && error.message.includes('500')) // Server error
    );
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
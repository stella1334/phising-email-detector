# Bank Phishing Guardian Extension Testing Guide

## Overview

This guide provides comprehensive testing procedures for the Bank Phishing Guardian browser extension to ensure reliable operation across different email providers and scenarios.

## Test Environment Setup

### Prerequisites
- Chrome browser (latest version)
- Bank Phishing Detector API running locally
- Test email accounts on supported providers
- Extension loaded in developer mode

### Test Email Accounts
Set up test accounts on:
- Gmail (mail.google.com)
- Outlook (outlook.live.com)
- Yahoo Mail (mail.yahoo.com)
- AOL Mail (mail.aol.com)

## Test Categories

### 1. Installation and Setup Tests

#### Test 1.1: Extension Installation
**Objective**: Verify extension installs correctly

**Steps**:
1. Open Chrome → Extensions (chrome://extensions/)
2. Enable Developer mode
3. Click "Load unpacked"
4. Select browser_extension folder
5. Verify extension appears in list

**Expected Results**:
- ✅ Extension loads without errors
- ✅ Extension icon appears in toolbar
- ✅ No console errors in browser

#### Test 1.2: Initial Configuration
**Objective**: Verify default settings work

**Steps**:
1. Click extension icon
2. Verify popup opens
3. Check default settings
4. Test API connection indicator

**Expected Results**:
- ✅ Popup displays correctly
- ✅ API status shows "Connected" or "Checking..."
- ✅ Default settings are reasonable

### 2. Email Provider Integration Tests

#### Test 2.1: Gmail Integration
**Provider**: mail.google.com

**Test Cases**:
```
TC2.1.1: Open Gmail inbox
- Navigate to Gmail
- Verify extension detects Gmail
- Check for provider-specific selectors

TC2.1.2: Open individual email
- Click on any email
- Wait for email to load
- Verify automatic analysis triggers
- Check for analysis indicator

TC2.1.3: Navigate between emails
- Open multiple emails in sequence
- Verify analysis updates for each
- Check for memory leaks
```

#### Test 2.2: Outlook Integration
**Provider**: outlook.live.com

**Test Cases**:
```
TC2.2.1: Outlook Web App
- Navigate to Outlook online
- Verify provider detection
- Test email selection

TC2.2.2: Office 365 Outlook
- Test on outlook.office.com
- Verify same functionality
- Check enterprise compatibility
```

#### Test 2.3: Yahoo Mail Integration
**Provider**: mail.yahoo.com

**Test Cases**:
```
TC2.3.1: Yahoo Mail interface
- Navigate to Yahoo Mail
- Test provider detection
- Verify email extraction
```

### 3. Analysis Functionality Tests

#### Test 3.1: Legitimate Email Analysis
**Objective**: Verify safe emails are correctly identified

**Test Emails**:
1. Bank statement from known legitimate bank
2. Newsletter from reputable source
3. Personal email from known contact
4. Automated system notification

**Steps**:
1. Open test email
2. Wait for analysis to complete
3. Check risk score and indicators
4. Verify no false alarms

**Expected Results**:
- ✅ Risk score < 40 (Low risk)
- ✅ Green safety indicator
- ✅ No warning overlays
- ✅ "Safe" status in popup

#### Test 3.2: Phishing Email Analysis
**Objective**: Verify suspicious emails trigger warnings

**Test Scenarios**:
1. Email with suspicious sender domain
2. Email with urgent language and credential requests
3. Email with shortened URLs
4. Email with suspicious attachments

**Steps**:
1. Create or find test phishing email
2. Open in email client
3. Wait for analysis
4. Check warning display

**Expected Results**:
- ✅ Risk score > 70 (High risk)
- ✅ Warning overlay appears
- ✅ Red danger indicator
- ✅ Specific threat details shown

#### Test 3.3: Manual Analysis
**Objective**: Test manual analysis trigger

**Steps**:
1. Open any email
2. Click extension icon
3. Click "Analyze Current Email"
4. Wait for results

**Expected Results**:
- ✅ Analysis starts immediately
- ✅ Loading indicator shows
- ✅ Results update in popup
- ✅ Button shows completion state

### 4. User Interface Tests

#### Test 4.1: Warning Overlay Display
**Objective**: Verify warning overlays work correctly

**Test Cases**:
```
TC4.1.1: Warning overlay appearance
- Trigger warning on phishing email
- Verify overlay positioning
- Check visual hierarchy
- Test responsive design

TC4.1.2: Overlay interaction
- Test close button
- Test action buttons
- Verify overlay dismissal
```

#### Test 4.2: Extension Popup
**Objective**: Test popup interface functionality

**Test Cases**:
```
TC4.2.1: Popup display
- Click extension icon
- Verify popup opens
- Check all sections load
- Test responsive layout

TC4.2.2: Settings interaction
- Open settings modal
- Modify settings
- Save changes
- Verify persistence

TC4.2.3: Activity display
- Perform multiple analyses
- Check activity updates
- Verify statistics accuracy
```

### 5. Settings and Configuration Tests

#### Test 5.1: Settings Persistence
**Objective**: Verify settings save and load correctly

**Steps**:
1. Open settings
2. Change multiple settings
3. Save settings
4. Reload extension
5. Verify settings retained

**Expected Results**:
- ✅ All settings persist across reloads
- ✅ Default values work correctly
- ✅ Invalid values handled gracefully

#### Test 5.2: API Endpoint Configuration
**Objective**: Test custom API endpoint

**Steps**:
1. Change API endpoint in settings
2. Save configuration
3. Test connection
4. Perform analysis

**Expected Results**:
- ✅ New endpoint saves correctly
- ✅ Connection test works
- ✅ Analysis uses new endpoint
- ✅ Fallback on connection failure

### 6. Performance Tests

#### Test 6.1: Memory Usage
**Objective**: Verify extension doesn't leak memory

**Steps**:
1. Open Chrome Task Manager
2. Note initial memory usage
3. Perform 50+ email analyses
4. Check memory usage

**Expected Results**:
- ✅ Memory usage stays reasonable
- ✅ No significant memory leaks
- ✅ CPU usage remains low

#### Test 6.2: Response Time
**Objective**: Measure analysis performance

**Steps**:
1. Time analysis completion
2. Test with different email sizes
3. Measure across providers

**Expected Results**:
- ✅ Analysis completes within 5 seconds
- ✅ No UI blocking during analysis
- ✅ Progress indicators work

### 7. Error Handling Tests

#### Test 7.1: API Unavailable
**Objective**: Test behavior when API is down

**Steps**:
1. Stop API service
2. Attempt email analysis
3. Check error handling
4. Restart API
5. Verify recovery

**Expected Results**:
- ✅ Graceful error message
- ✅ No extension crash
- ✅ Automatic retry logic
- ✅ Recovery when API returns

#### Test 7.2: Network Timeouts
**Objective**: Test timeout handling

**Steps**:
1. Simulate slow network
2. Trigger analysis
3. Wait for timeout
4. Check error handling

**Expected Results**:
- ✅ Timeout handled gracefully
- ✅ User notified of issue
- ✅ Extension remains functional

#### Test 7.3: Invalid Email Content
**Objective**: Test with malformed emails

**Steps**:
1. Create emails with missing elements
2. Test with non-standard formatting
3. Verify error handling

**Expected Results**:
- ✅ No crashes on invalid content
- ✅ Fallback analysis modes work
- ✅ Meaningful error messages

### 8. Security Tests

#### Test 8.1: Content Security Policy
**Objective**: Verify CSP compliance

**Steps**:
1. Check browser console for CSP violations
2. Test on different email providers
3. Verify no unsafe evaluations

**Expected Results**:
- ✅ No CSP violations
- ✅ Safe script execution
- ✅ Proper content isolation

#### Test 8.2: Data Privacy
**Objective**: Verify data handling practices

**Steps**:
1. Analyze sensitive email content
2. Check data transmission
3. Verify local storage

**Expected Results**:
- ✅ Minimal data transmitted
- ✅ No persistent email storage
- ✅ Proper data sanitization

### 9. Cross-Browser Compatibility

#### Test 9.1: Chrome Versions
**Objective**: Test across Chrome versions

**Browsers to Test**:
- Chrome Stable (latest)
- Chrome Beta
- Chromium
- Microsoft Edge (Chromium)

#### Test 9.2: Mobile Compatibility
**Objective**: Test on mobile Chrome

**Note**: Limited functionality expected on mobile browsers

### 10. Regression Tests

After any code changes, run the following regression test suite:

#### Quick Regression (15 minutes)
1. Extension installs correctly
2. Gmail integration works
3. Safe email shows green indicator
4. Phishing email shows warning
5. Settings can be modified

#### Full Regression (2 hours)
1. All provider integrations
2. Complete UI functionality
3. Error handling scenarios
4. Performance benchmarks
5. Security validations

## Test Automation

### Automated Test Scripts

```javascript
// Example automated test using Selenium
const { Builder, By, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');

async function testGmailIntegration() {
  const options = new chrome.Options();
  options.addArguments('--load-extension=./browser_extension');
  
  const driver = new Builder()
    .forBrowser('chrome')
    .setChromeOptions(options)
    .build();
  
  try {
    await driver.get('https://mail.google.com');
    
    // Wait for page load
    await driver.wait(until.titleContains('Gmail'), 10000);
    
    // Test extension presence
    const extensionIcon = await driver.findElement(By.css('[data-extension-id]'));
    assert(extensionIcon, 'Extension icon should be present');
    
    console.log('Gmail integration test passed');
  } finally {
    await driver.quit();
  }
}
```

## Test Reporting

### Test Results Template

```
Bank Phishing Guardian Extension Test Report
Date: [DATE]
Tester: [NAME]
Version: [VERSION]

## Test Summary
- Total Tests: [TOTAL]
- Passed: [PASSED]
- Failed: [FAILED]
- Skipped: [SKIPPED]

## Failed Tests
[List any failed tests with details]

## Performance Metrics
- Average Analysis Time: [TIME]ms
- Memory Usage: [MEMORY]MB
- CPU Usage: [CPU]%

## Browser Compatibility
- Chrome: [STATUS]
- Edge: [STATUS]
- Firefox: [STATUS]

## Recommendations
[Any improvements or fixes needed]
```

## Continuous Testing

### Daily Smoke Tests
- Basic functionality check
- API connectivity test
- Critical path verification

### Weekly Full Tests
- Complete test suite execution
- Performance benchmarking
- Security validation

### Pre-Release Testing
- Full regression test suite
- Cross-browser compatibility
- Load testing
- Security audit

This comprehensive testing guide ensures the Bank Phishing Guardian extension works reliably across all supported scenarios and provides a robust user experience.
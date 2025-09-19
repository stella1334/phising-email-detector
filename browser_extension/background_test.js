// Simple test script to verify background script connectivity
// Run this in the browser console to test if the background script responds

console.log('🧪 Testing background script connectivity...');

// Test basic message sending
chrome.runtime.sendMessage({
  action: 'healthCheck'
}, (response) => {
  if (chrome.runtime.lastError) {
    console.error('❌ Chrome runtime error:', chrome.runtime.lastError);
  } else {
    console.log('✅ Background script responded:', response);
  }
});

// Test with timeout
const testWithTimeout = new Promise((resolve, reject) => {
  const timeout = setTimeout(() => {
    reject(new Error('Background script response timeout'));
  }, 5000);
  
  chrome.runtime.sendMessage({
    action: 'healthCheck'
  }, (response) => {
    clearTimeout(timeout);
    if (chrome.runtime.lastError) {
      reject(new Error('Chrome runtime error: ' + chrome.runtime.lastError.message));
    } else {
      resolve(response);
    }
  });
});

testWithTimeout
  .then(response => {
    console.log('✅ Background script test passed:', response);
  })
  .catch(error => {
    console.error('❌ Background script test failed:', error);
  });
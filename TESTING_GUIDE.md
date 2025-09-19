# 🛠️ Complete Extension Testing & Troubleshooting Guide

## **What Was Fixed:**

### ✅ **Fixed Gmail Content Detection**
- Updated selectors to work with Gmail's current 2025 interface
- Added multiple fallback selectors for subject, sender, and body
- Improved email extraction with better error handling

### ✅ **Fixed Python API Server Errors**
- Fixed string formatting error in Gemini analyzer (`<score_0_to_100>` issue)
- Added proper error handling for undefined responses
- Improved Pydantic settings import

### ✅ **Fixed JavaScript Runtime Errors** 
- Added proper validation for API responses
- Better error handling for undefined objects
- Improved extension messaging reliability

---

## **Step-by-Step Testing Process:**

### **1. Start the API Server**

```bash
cd bank_phishing_detector

# Make sure you have a valid Gemini API key in .env file
# GEMINI_API_KEY=your_actual_api_key_here

python app.py
```

**Expected Output:**
```
✅ Server starting on http://localhost:8000
✅ Gemini API connectivity test: PASSED
✅ Application startup complete
```

### **2. Load Extension in Chrome**

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select the `bank_phishing_detector/browser_extension/` folder
5. You should see "Bank Phishing Guardian" in your extensions list

### **3. Test Extension Setup**

1. **Click the extension icon** in Chrome toolbar
2. **Configure settings:**
   - API URL: `http://localhost:8000`
   - Enable Detection: ON
   - Click Save

### **4. Test Email Reading (Most Important)**

1. **Open Gmail** (https://mail.google.com)
2. **Open any email** (click on an email to view its content)
3. **Test extraction manually:**
   - Press `F12` to open Developer Tools
   - Go to **Console** tab
   - Type: `window.bpgExtension.extractEmailData()`
   - Press Enter

**Expected Result:**
```javascript
{
  provider: "gmail",
  subject: "Your email subject here",
  sender: "sender@example.com", 
  bodyText: "Email content text...",
  links: [...],
  // ... other data
}
```

### **5. Test Manual Analysis**

1. **With an email open in Gmail:**
2. **Click extension icon** → **"Analyze Current Email"**
3. **Watch for results:**
   - Button should show "Analyzing..." then "Analysis Started"
   - Check browser console for any errors
   - Look for visual indicators around the email

---

## **Debugging Tools:**

### **Browser Console Debugging**

Open Gmail, press F12, and run these commands:

```javascript
// Enable debug mode
localStorage.setItem('phishing-debug', 'true');

// Test email extraction
window.bpgExtension.extractEmailData();

// Test analysis
window.bpgExtension.analyzeCurrentEmail();

// Check extension status
chrome.runtime.sendMessage({action: 'getSettings'}).then(console.log);
```

### **Server-Side Debugging**

Monitor the Python server console for these logs:
```bash
INFO | Email analysis request received from: gmail
INFO | Deterministic checks completed. Score: XX.X
INFO | Gemini analysis completed. Phishing likelihood: XX%
INFO | Final risk score: XX.X (LEVEL)
```

---

## **Common Issues & Solutions:**

### **❌ "Failed to analyze email" Error**

**Causes & Solutions:**

1. **No email content detected:**
   ```javascript
   // Test in console:
   document.querySelectorAll('.ii.gt div, .a3s.aiL').length
   // Should return > 0 if email is open
   ```
   **Solution:** Make sure you've clicked on an email to open it fully

2. **Gmail interface changes:**
   ```javascript
   // Check current Gmail structure:
   document.querySelectorAll('[role="main"]').length
   ```
   **Solution:** Gmail structure may have changed, selectors need updating

3. **Extension permissions:**
   - Check `chrome://extensions/` → Bank Phishing Guardian → Details
   - Ensure "Allow on all sites" is enabled

### **❌ API Connection Errors**

**Test API manually:**
```bash
curl http://localhost:8000/health
```

**Common fixes:**
- Ensure Python server is running
- Check firewall isn't blocking port 8000
- Verify Gemini API key is valid

### **❌ Extension Not Loading**

1. **Check manifest errors:**
   - Go to `chrome://extensions/`
   - Look for red error messages
   
2. **Reload extension:**
   - Click refresh icon on extension card
   - Or remove and re-add the extension

---

## **Expected Behavior When Working:**

### **Visual Indicators**
- **Green border:** Safe email (low risk score)
- **Yellow border:** Suspicious email (medium risk)
- **Red border:** Dangerous email (high risk)

### **Console Logs**
```
Bank Phishing Guardian: Initializing on gmail
Found subject: [email subject]
Found sender: [sender email]
Found body text length: [number]
Successfully extracted email data: {...}
✅ Extension messaging works
```

### **Server Logs**
```
INFO | POST /analyze 200 OK
INFO | Gemini analysis completed. Phishing likelihood: 25%
INFO | Final risk score: 32.5 (LOW)
```

---

## **Manual Testing Checklist:**

- [ ] API server starts without errors
- [ ] Extension loads in Chrome without manifest errors
- [ ] Extension icon appears in toolbar
- [ ] Can configure settings in popup
- [ ] Gmail page loads with extension active
- [ ] Email content extraction works (console test)
- [ ] Manual analysis button works
- [ ] Visual indicators appear around emails
- [ ] Server receives and processes analysis requests
- [ ] No JavaScript errors in browser console
- [ ] No Python errors in server console

---

## **Getting Help:**

If issues persist:
1. **Check browser console** for JavaScript errors
2. **Check server console** for Python errors  
3. **Test API manually** with curl
4. **Try different emails** (some might have unusual structure)
5. **Refresh the Gmail page** and try again

The most common issue is Gmail's DOM structure not matching our selectors. The improved extraction function should handle this better now.

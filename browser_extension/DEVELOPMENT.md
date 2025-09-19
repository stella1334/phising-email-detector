# Bank Phishing Guardian - Development Guide

## Development Setup

### Prerequisites
- Node.js 14+ (for build tools)
- Chrome/Chromium browser
- Bank Phishing Detector API running

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd bank_phishing_detector/browser_extension

# Install development dependencies (optional)
npm install -g uglify-js csso-cli

# Make build script executable
chmod +x build.sh
```

### Loading Extension in Development

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `browser_extension` directory
5. Extension will appear in your extensions list

### Development Workflow

1. **Make Changes**: Edit source files
2. **Reload Extension**: Click reload button in `chrome://extensions/`
3. **Test Changes**: Navigate to email provider and test
4. **Debug**: Use browser console (F12) to view logs

## Architecture Overview

### Component Communication Flow

```
Email Page (Gmail/Outlook)
    ↓
Content Script (content.js)
    ↓
Background Service Worker (background.js)
    ↓
API Service (localhost:8000)
    ↓
Analysis Results
    ↓
UI Updates (Warning Overlays)
```

### File Responsibilities

#### Core Extension Files
- **`manifest.json`**: Extension configuration and permissions
- **`background.js`**: Service worker for API communication
- **`content.js`**: Injected script for email page interaction
- **`popup.js`**: Extension popup interface logic

#### Support Files
- **`api.js`**: API client with retry logic
- **`storage.js`**: Settings and data management
- **`content.css`**: Styling for warning overlays
- **`popup.css`**: Popup interface styling

## Email Provider Integration

### Adding New Email Providers

1. **Update Manifest**: Add host permissions
2. **Update Content Script**: Add provider detection
3. **Add Selectors**: Define CSS selectors for email elements
4. **Test Integration**: Verify email extraction works

#### Example: Adding ProtonMail Support

```javascript
// In content.js
detectProvider() {
  const hostname = window.location.hostname;
  
  if (hostname.includes('mail.proton.me')) {
    return 'protonmail';
  }
  // ... existing providers
}

// Add selectors
getSelectors() {
  const selectors = {
    protonmail: {
      emailSubject: '[data-testid="message:subject"]',
      emailSender: '[data-testid="message:sender"]',
      emailBody: '[data-testid="message-content"]',
      emailDate: '[data-testid="message:date"]'
    },
    // ... existing selectors
  };
}
```

### Email Extraction Challenges

#### Dynamic Content
- **Problem**: Email content loaded via AJAX
- **Solution**: Use MutationObserver to detect changes
- **Implementation**: Debounced analysis triggers

#### Security Restrictions
- **Problem**: CSP headers block script injection
- **Solution**: Use content scripts with proper permissions
- **Implementation**: Isolated world execution

#### Provider Differences
- **Problem**: Different DOM structures across providers
- **Solution**: Provider-specific selectors and extraction logic
- **Implementation**: Adapter pattern for each provider

## API Integration

### Request Flow

1. **Content Script** extracts email data
2. **Background Script** receives data via message passing
3. **API Client** formats and sends request
4. **Retry Logic** handles failures and timeouts
5. **Response Processing** formats results for UI

### Error Handling

```javascript
// Example error handling in api.js
async function makeRequest(method, endpoint, data, attempt = 1) {
  try {
    // ... make request
  } catch (error) {
    if (attempt < this.retryAttempts && this.shouldRetry(error)) {
      await this.delay(attempt * 1000);
      return this.makeRequest(method, endpoint, data, attempt + 1);
    }
    throw error;
  }
}
```

### Rate Limiting

- **Client-side**: Debounce analysis requests
- **Server-side**: Respect API rate limits
- **Fallback**: Show cached results when API unavailable

## UI/UX Design

### Warning Overlay Design Principles

1. **Non-intrusive**: Don't block email reading
2. **Clear Hierarchy**: Risk level immediately visible
3. **Actionable**: Provide clear next steps
4. **Dismissible**: Allow users to close warnings
5. **Accessible**: Support screen readers and keyboard navigation

### Responsive Design

```css
/* Example responsive breakpoints */
@media (max-width: 768px) {
  .bpg-warning-overlay {
    width: 90vw;
    top: 10px;
    right: 5vw;
  }
}
```

### Dark Mode Support

```css
@media (prefers-color-scheme: dark) {
  .bpg-warning-overlay {
    background: #2d2d2d;
    color: #e0e0e0;
  }
}
```

## Performance Optimization

### Content Script Performance

- **Lazy Loading**: Only inject when email detected
- **Debouncing**: Avoid excessive API calls
- **Caching**: Store analysis results locally
- **DOM Efficiency**: Minimize DOM queries

### Memory Management

```javascript
// Clean up observers on page unload
window.addEventListener('beforeunload', () => {
  this.observers.forEach(observer => observer.disconnect());
  this.removeAnalysisOverlay();
});
```

### Bundle Size Optimization

- **Tree Shaking**: Remove unused code
- **Minification**: Compress JavaScript and CSS
- **Image Optimization**: Use efficient icon formats
- **Lazy Loading**: Load components on demand

## Testing

### Manual Testing Checklist

#### Basic Functionality
- [ ] Extension installs without errors
- [ ] Popup opens and displays correctly
- [ ] Settings can be modified and saved
- [ ] API connection status is accurate

#### Email Analysis
- [ ] Legitimate emails show safe indicators
- [ ] Phishing emails trigger warnings
- [ ] Manual analysis works via popup
- [ ] Warning overlays display correctly

#### Cross-Provider Testing
- [ ] Gmail integration works
- [ ] Outlook integration works
- [ ] Yahoo Mail integration works
- [ ] Provider-specific selectors function

#### Error Scenarios
- [ ] API unavailable gracefully handled
- [ ] Network timeouts don't crash extension
- [ ] Invalid email content handled safely
- [ ] Permission errors show helpful messages

### Automated Testing

```javascript
// Example unit test
describe('Email Extractor', () => {
  test('should extract sender email correctly', () => {
    const mockElement = {
      getAttribute: jest.fn().mockReturnValue('test@example.com'),
      textContent: 'John Doe <test@example.com>'
    };
    
    const result = extractor.extractEmailAddress(mockElement);
    expect(result).toBe('test@example.com');
  });
});
```

## Security Considerations

### Content Security Policy

- **Avoid eval()**: Use safe alternatives
- **Sanitize HTML**: Prevent XSS in overlays
- **Validate Inputs**: Check all user inputs
- **Secure Communication**: Use HTTPS for API calls

### Data Privacy

- **Minimal Data**: Only extract necessary information
- **Local Processing**: Analyze locally when possible
- **User Consent**: Clear privacy settings
- **Data Retention**: Automatic cleanup of stored data

### Permission Management

```json
// Minimal permissions in manifest.json
{
  "permissions": [
    "activeTab",    // Only current tab access
    "storage",      // User preferences only
    "scripting"     // Content script injection
  ]
}
```

## Debugging

### Common Issues

#### Extension Not Loading
- Check manifest.json syntax
- Verify all referenced files exist
- Review browser console for errors
- Check permissions in manifest

#### Content Script Failures
- Ensure proper host permissions
- Check CSP compatibility
- Verify DOM selectors are current
- Test on different email providers

#### API Communication Issues
- Verify API service is running
- Check CORS configuration
- Test endpoint directly with curl
- Review network tab in DevTools

### Debug Tools

```javascript
// Debug logging
const DEBUG = true; // Set to false for production

function debugLog(message, data = null) {
  if (DEBUG) {
    console.log(`[BPG Debug] ${message}`, data);
  }
}
```

### Performance Profiling

1. Open Chrome DevTools
2. Go to Performance tab
3. Record while using extension
4. Analyze for bottlenecks
5. Optimize slow operations

## Release Process

### Version Management

1. **Update Version**: Increment in manifest.json
2. **Update Changelog**: Document new features/fixes
3. **Test Thoroughly**: Full regression testing
4. **Build Package**: Run build.sh script
5. **Submit to Store**: Upload to Chrome Web Store

### Chrome Web Store Submission

1. **Prepare Assets**:
   - Extension zip file
   - Screenshots (1280x800)
   - Promotional images
   - Store description

2. **Store Listing**:
   - Clear, compelling description
   - Relevant keywords
   - Privacy policy link
   - Support contact information

3. **Review Process**:
   - Automated security scan
   - Manual review (can take days)
   - Possible rejection and revision

## Contributing

### Code Style

- **JavaScript**: Use ES6+ features
- **Naming**: camelCase for variables, PascalCase for classes
- **Comments**: JSDoc for functions, inline for complex logic
- **Formatting**: 2-space indentation, semicolons required

### Git Workflow

1. **Fork Repository**: Create your own fork
2. **Feature Branch**: Create branch for each feature
3. **Commit Messages**: Use conventional commit format
4. **Pull Request**: Submit PR with description
5. **Code Review**: Address reviewer feedback

### Documentation

- **Code Comments**: Explain complex logic
- **README Updates**: Document new features
- **API Changes**: Update integration docs
- **User Guide**: Keep instructions current

This development guide should help contributors understand the extension architecture and development process. For specific implementation questions, refer to the inline code comments and test the extension thoroughly across different scenarios.
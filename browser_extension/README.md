# Bank Phishing Guardian - Browser Extension

A powerful browser extension that provides real-time phishing detection for your emails, powered by AI and advanced threat analysis.

## Features

### 🛡️ Real-Time Protection
- **Automatic Email Analysis**: Scans emails as you read them
- **AI-Powered Detection**: Uses Google Gemini for semantic analysis
- **Multi-Layer Security**: Combines deterministic rules with machine learning
- **Visual Warnings**: Clear, non-intrusive alerts for suspicious emails

### 📧 Email Provider Support
- **Gmail** (mail.google.com)
- **Outlook** (outlook.live.com, outlook.office.com)
- **Yahoo Mail** (mail.yahoo.com)
- **AOL Mail** (mail.aol.com)

### 🎯 Advanced Detection
- **URL Analysis**: Suspicious links and domains
- **Content Scanning**: Phishing language patterns
- **Header Validation**: SPF, DKIM, DMARC checks
- **Attachment Security**: Dangerous file detection
- **Sender Reputation**: Domain trustworthiness

### ⚙️ Customizable Settings
- **Sensitivity Levels**: Adjust detection threshold
- **Auto-Analysis**: Enable/disable automatic scanning
- **Warning Display**: Control overlay visibility
- **Privacy Controls**: Manage data collection

## Installation

### Option 1: Install from Chrome Web Store (Recommended)
*Coming soon - Extension pending review*

### Option 2: Manual Installation (Developer Mode)

1. **Download the Extension**:
   ```bash
   git clone <repository-url>
   cd bank_phishing_detector/browser_extension
   ```

2. **Open Chrome Extensions**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

3. **Load Extension**:
   - Click "Load unpacked"
   - Select the `browser_extension` folder
   - Extension should appear in your extensions list

4. **Pin Extension** (Optional):
   - Click the puzzle piece icon in Chrome toolbar
   - Pin "Bank Phishing Guardian" for easy access

## Setup

### 1. Start the API Service

First, ensure the Bank Phishing Detector API is running:

```bash
cd bank_phishing_detector
# Copy and configure environment
cp .env.example .env
# Edit .env with your Gemini API key

# Install dependencies
pip install -r requirements.txt

# Start the service
python app.py
```

The API should be running at `http://localhost:8000`

### 2. Configure Extension

1. Click the extension icon in your browser
2. Click "Settings" button
3. Verify API endpoint is set to `http://localhost:8000`
4. Adjust sensitivity and preferences
5. Click "Save Settings"

### 3. Test the Extension

1. Navigate to Gmail, Outlook, or another supported email provider
2. Open any email
3. The extension should automatically analyze the email
4. Look for:
   - Green checkmark: Safe email
   - Warning overlay: Suspicious content detected
   - Red alert: High-risk phishing attempt

## Usage

### Automatic Analysis
Once installed and configured, the extension automatically:
- Detects when you're viewing an email
- Extracts email content and metadata
- Sends data to the API for analysis
- Displays results with visual indicators

### Manual Analysis
- Click the extension icon
- Click "Analyze Current Email" button
- View detailed results in the popup

### Understanding Results

#### Risk Scores
- **0-39**: Low risk (Safe)
- **40-69**: Medium risk (Caution)
- **70-89**: High risk (Warning)
- **90-100**: Critical risk (Danger)

#### Warning Indicators
- **🟢 Green**: Email appears safe
- **🟡 Yellow**: Some suspicious elements
- **🔴 Red**: High risk - exercise extreme caution

### Privacy Features

#### Data Handling
- **Local Processing**: Email content analyzed securely
- **No Storage**: Emails not permanently stored
- **Anonymized Analytics**: Only aggregate statistics collected
- **User Control**: Disable analytics collection anytime

#### Security
- **HTTPS Communication**: Encrypted API calls
- **Content Security**: No external scripts loaded
- **Permission Minimal**: Only necessary browser permissions

## Configuration

### Extension Settings

| Setting | Description | Default |
|---------|-------------|----------|
| Enable Protection | Turn extension on/off | Enabled |
| Detection Sensitivity | Low/Medium/High sensitivity | Medium |
| Auto-analyze | Automatic email scanning | Enabled |
| Show Warnings | Display warning overlays | Enabled |
| Collect Analytics | Anonymous usage statistics | Enabled |
| API Endpoint | Backend service URL | localhost:8000 |

### Advanced Configuration

For advanced users, you can modify:
- API timeout settings
- Retry logic parameters
- Cache duration
- UI positioning

## Troubleshooting

### Common Issues

#### Extension Not Working
1. Check if API service is running (`http://localhost:8000/health`)
2. Verify extension is enabled in Chrome
3. Refresh the email page
4. Check browser console for errors (F12)

#### No Analysis Results
1. Ensure you're on a supported email provider
2. Check that you're viewing an email (not inbox)
3. Verify API endpoint in settings
4. Test manual analysis via popup

#### Poor Detection Accuracy
1. Adjust sensitivity settings
2. Update to latest extension version
3. Check API service logs
4. Report false positives/negatives

### Debug Mode

1. Open browser console (F12)
2. Look for "Bank Phishing Guardian" log messages
3. Check for API connection errors
4. Verify content script injection

### API Connection Issues

```bash
# Test API directly
curl http://localhost:8000/health

# Check API logs
tail -f logs/phishing_detector.log
```

## Development

### File Structure
```
browser_extension/
├── manifest.json          # Extension manifest
├── background.js          # Service worker
├── content.js            # Content script injection
├── content.css           # Styling for warnings
├── popup.html            # Extension popup UI
├── popup.css             # Popup styling
├── popup.js              # Popup functionality
├── api.js                # API communication
├── storage.js            # Data storage management
└── icons/                # Extension icons
```

### Building for Production

1. **Update Manifest**:
   - Change API endpoint to production URL
   - Update version number
   - Add production host permissions

2. **Package Extension**:
   ```bash
   # Create zip file for Chrome Web Store
   zip -r bank-phishing-guardian.zip . -x "*.git*" "README.md"
   ```

3. **Test Thoroughly**:
   - Test on all supported email providers
   - Verify API connectivity
   - Check performance impact
   - Validate privacy compliance

### Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

### Browser Compatibility

- **Chrome**: Fully supported (Manifest V3)
- **Edge**: Compatible (Chromium-based)
- **Firefox**: Requires manifest conversion
- **Safari**: Not yet supported

## Privacy & Security

### Data Collection
- **What we collect**: Anonymous usage statistics, threat detection metrics
- **What we don't collect**: Email content, personal information, credentials
- **Data retention**: Local analytics cleared after 30 days
- **Sharing**: No data shared with third parties

### Permissions Explained
- **activeTab**: Access current email page for analysis
- **storage**: Save user preferences and settings
- **scripting**: Inject analysis scripts into email pages
- **host permissions**: Communicate with email providers and API

## Support

### Getting Help
- **Documentation**: See main project README
- **Issues**: GitHub issue tracker
- **Discord**: Community support channel
- **Email**: support@bankphishingguardian.com

### Reporting Bugs
Please include:
- Browser version
- Extension version
- Email provider
- Steps to reproduce
- Console error messages

## License

MIT License - see LICENSE file for details.

---

**⚠️ Important Security Note**: This extension is designed to enhance your email security but should not be your only line of defense. Always exercise caution with suspicious emails and verify sender authenticity through alternative channels.
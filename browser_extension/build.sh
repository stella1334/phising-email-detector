#!/bin/bash

# Build script for Bank Phishing Guardian Browser Extension

set -e

EXTENSION_DIR="browser_extension"
BUILD_DIR="build"
VERSION=$(grep '"version"' manifest.json | cut -d'"' -f4)
ARCHIVE_NAME="bank-phishing-guardian-v${VERSION}.zip"

echo "Building Bank Phishing Guardian Browser Extension v${VERSION}"
echo "========================================================"

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

# Create build directory
mkdir -p "$BUILD_DIR"

# Copy extension files
echo "Copying extension files..."
cp -r *.js *.json *.html *.css *.md "$BUILD_DIR/" 2>/dev/null || true

# Create icons directory if it doesn't exist
if [ ! -d "icons" ]; then
    echo "Creating placeholder icons..."
    mkdir -p "$BUILD_DIR/icons"
    
    # Create simple placeholder icons (you should replace these with actual icons)
    for size in 16 32 48 128; do
        # Create a simple colored square as placeholder
        echo "Creating ${size}x${size} icon placeholder..."
        # In a real build, you'd use ImageMagick or similar:
        # convert -size ${size}x${size} xc:'#667eea' "$BUILD_DIR/icons/icon${size}.png"
        
        # For now, create empty files as placeholders
        touch "$BUILD_DIR/icons/icon${size}.png"
    done
else
    cp -r icons "$BUILD_DIR/"
fi

# Validate manifest
echo "Validating manifest.json..."
if ! python3 -m json.tool "$BUILD_DIR/manifest.json" > /dev/null; then
    echo "❌ Invalid manifest.json"
    exit 1
fi

# Check required files
REQUIRED_FILES=(
    "manifest.json"
    "background.js"
    "content.js"
    "content.css"
    "popup.html"
    "popup.css"
    "popup.js"
    "api.js"
    "storage.js"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$BUILD_DIR/$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Minify JavaScript files (optional - requires uglify-js)
if command -v uglifyjs &> /dev/null; then
    echo "Minifying JavaScript files..."
    
    for js_file in "$BUILD_DIR"/*.js; do
        if [ -f "$js_file" ]; then
            echo "  Minifying $(basename "$js_file")..."
            uglifyjs "$js_file" -c -m -o "$js_file.min"
            mv "$js_file.min" "$js_file"
        fi
    done
else
    echo "⚠️  uglify-js not found - skipping minification"
fi

# Minify CSS files (optional - requires csso)
if command -v csso &> /dev/null; then
    echo "Minifying CSS files..."
    
    for css_file in "$BUILD_DIR"/*.css; do
        if [ -f "$css_file" ]; then
            echo "  Minifying $(basename "$css_file")..."
            csso "$css_file" --output "$css_file"
        fi
    done
else
    echo "⚠️  csso not found - skipping CSS minification"
fi

# Create zip archive
echo "Creating extension archive..."
cd "$BUILD_DIR"
zip -r "../$ARCHIVE_NAME" . -x "*.DS_Store" "*.git*"
cd ..

# Calculate file size
SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)

echo ""
echo "✅ Build completed successfully!"
echo "📦 Archive: $ARCHIVE_NAME ($SIZE)"
echo "📁 Build directory: $BUILD_DIR"
echo ""
echo "Next steps:"
echo "1. Test the extension by loading the build directory in Chrome"
echo "2. Upload $ARCHIVE_NAME to Chrome Web Store"
echo "3. Update version number for next release"
echo ""

# Validate the archive
echo "Validating archive contents..."
unzip -t "$ARCHIVE_NAME" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Archive is valid"
else
    echo "❌ Archive validation failed"
    exit 1
fi

echo "Build process complete! 🎉"
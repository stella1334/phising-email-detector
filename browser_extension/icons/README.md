# Icon Placeholder Files

This directory should contain the following icon files for the browser extension:

## Required Icons

- `icon16.png` - 16x16px - Extension toolbar icon (small)
- `icon32.png` - 32x32px - Extension popup and settings
- `icon48.png` - 48x48px - Extension management page
- `icon128.png` - 128x128px - Chrome Web Store listing

## Icon Design Guidelines

### Visual Style
- **Color Scheme**: Blue and purple gradient (#667eea to #764ba2)
- **Symbol**: Shield with checkmark or security-themed icon
- **Style**: Modern, flat design with subtle depth
- **Background**: Transparent or subtle gradient

### Technical Requirements
- **Format**: PNG with transparency
- **Resolution**: Exact pixel dimensions required
- **Quality**: High-quality, crisp edges
- **Accessibility**: Clear contrast and recognizable at small sizes

### Icon Creation Tools
- **Professional**: Adobe Illustrator, Figma, Sketch
- **Free**: GIMP, Inkscape, Canva
- **Online**: Favicon.io, IconMaker, Logo Maker

### Sample Icon Description
```
A modern shield icon with:
- Blue-to-purple gradient background
- White checkmark or security symbol
- Subtle shadow or glow effect
- Clean, professional appearance
```

## Creating Icons

To create actual icons, use this process:

1. **Design Base Icon** (128x128):
   ```bash
   # Using ImageMagick (example)
   convert -size 128x128 xc:'#667eea' \
     -fill white -gravity center \
     -pointsize 64 -annotate +0+0 '🛡️' \
     icon128.png
   ```

2. **Generate Smaller Sizes**:
   ```bash
   convert icon128.png -resize 48x48 icon48.png
   convert icon128.png -resize 32x32 icon32.png
   convert icon128.png -resize 16x16 icon16.png
   ```

3. **Optimize for Web**:
   ```bash
   # Reduce file size while maintaining quality
   pngcrush -reduce -brute icon*.png
   ```

## Placeholder Note

The current build script will create empty placeholder files for development.
Replace these with actual icon files before production deployment.

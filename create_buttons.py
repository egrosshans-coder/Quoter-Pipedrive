#!/usr/bin/env python3
"""
Create button images for testing
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create buttons directory
os.makedirs('static/buttons', exist_ok=True)

# Button dimensions
width, height = 200, 50

# Create green "View Online" button
green_button = Image.new('RGB', (width, height), color='#28a745')
draw = ImageDraw.Draw(green_button)

# Try to use a system font, fallback to default
try:
    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
except:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()

# Get text dimensions for centering
text = "View Online"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

# Draw text centered
x = (width - text_width) // 2
y = (height - text_height) // 2
draw.text((x, y), text, fill='white', font=font)

# Save green button
green_button.save('static/buttons/button-view-online.png')

# Create blue "Download PDF" button
blue_button = Image.new('RGB', (width, height), color='#007bff')
draw = ImageDraw.Draw(blue_button)

# Draw text centered
text = "Download PDF"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

x = (width - text_width) // 2
y = (height - text_height) // 2
draw.text((x, y), text, fill='white', font=font)

# Save blue button
blue_button.save('static/buttons/button-download-pdf.png')

print("✅ Created button images:")
print("   - static/buttons/button-view-online.png")
print("   - static/buttons/button-download-pdf.png")

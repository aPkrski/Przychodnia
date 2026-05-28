#!/usr/bin/env python3
"""
Generate app icon (ICO) for PoradniaFinanceApp using PIL.
This script creates a professional medical + finance themed icon.

Usage:
    python generate_icon.py
"""

from PIL import Image, ImageDraw
import os


def create_app_icon(output_path: str = "assets/app_icon.ico", size: int = 256):
    """
    Create a professional icon combining medical (cross) and financial (chart) symbols.
    
    Args:
        output_path: Path where to save the .ico file
        size: Icon size (default 256x256)
    """
    # Create a new image with white background
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Define colors
    blue = (37, 99, 235)  # Medical blue
    dark_blue = (30, 64, 175)
    green = (16, 185, 129)  # Finance green
    dark_green = (5, 150, 105)
    white = (255, 255, 255)
    gray = (107, 114, 128)
    
    # Proportions
    padding = size // 8
    circle_radius = size // 6
    
    # Left circle - Medical (blue gradient simulated with two circles)
    left_x = size // 4
    left_y = size // 2 - 20
    draw.ellipse([left_x - circle_radius, left_y - circle_radius, 
                  left_x + circle_radius, left_y + circle_radius], 
                 fill=blue, outline=dark_blue, width=2)
    
    # Medical cross in left circle
    cross_width = circle_radius // 4
    cross_length = circle_radius * 1.3
    # Vertical bar
    draw.rectangle([left_x - cross_width, left_y - cross_length,
                    left_x + cross_width, left_y + cross_length],
                   fill=white)
    # Horizontal bar
    draw.rectangle([left_x - cross_length, left_y - cross_width,
                    left_x + cross_length, left_y + cross_width],
                   fill=white)
    
    # Right circle - Finance (green)
    right_x = (size * 3) // 4
    right_y = size // 2 + 20
    draw.ellipse([right_x - circle_radius, right_y - circle_radius,
                  right_x + circle_radius, right_y + circle_radius],
                 fill=green, outline=dark_green, width=2)
    
    # Chart bars in right circle
    bar_width = circle_radius // 3
    bar_spacing = bar_width + 5
    bar_heights = [circle_radius // 2, circle_radius // 1.2, circle_radius * 1.3]
    
    for i, height in enumerate(bar_heights):
        x_offset = right_x - bar_width - bar_spacing
        x_pos = x_offset + (i * bar_spacing)
        draw.rectangle([x_pos, right_y + circle_radius // 3 - height,
                        x_pos + bar_width, right_y + circle_radius // 3],
                       fill=white)
    
    # Up arrow on chart
    arrow_x = right_x + circle_radius // 2
    arrow_y = right_y - circle_radius // 2
    arrow_size = 8
    # Arrow head
    points = [
        (arrow_x, arrow_y - arrow_size),
        (arrow_x - arrow_size, arrow_y),
        (arrow_x + arrow_size, arrow_y),
    ]
    draw.polygon(points, fill=white)
    # Arrow line
    draw.line([(arrow_x, arrow_y), (arrow_x, arrow_y + arrow_size)],
              fill=white, width=3)
    
    # Connector line between circles (subtle)
    mid_x = (left_x + right_x) // 2
    mid_y = (left_y + right_y) // 2
    draw.line([(left_x + circle_radius // 1.5, left_y + circle_radius // 2),
               (right_x - circle_radius // 1.5, right_y - circle_radius // 2)],
              fill=gray, width=2)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    # Save as ICO with multiple sizes for better compatibility
    # ICO format supports multiple sizes
    img.save(output_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print(f"✓ Icon created: {output_path}")
    
    # Also save as PNG for reference
    png_path = output_path.replace('.ico', '.png')
    img.save(png_path, format='PNG')
    print(f"✓ PNG reference saved: {png_path}")


if __name__ == "__main__":
    create_app_icon()
    print("\nIcon generation complete!")
    print("You can now build the executable with: build_exe.ps1 or build_exe.bat")

# QR Code Reader - Main Module

## Description
`main.py` is the core module of a QR Code Reader project that analyzes QR code images and generates an SVG visualization with detected patterns highlighted. It identifies timing patterns (in gold) and finder patterns (in blue) to understand the QR code structure and prepares the data for further decoding.

## Features
- Processes QR code images using run-length encoding (RLE) for pattern detection
- Identifies timing patterns (alternating black/white modules)
- Locates finder patterns (square markers at corners)
- Generates SVG output overlays to visualize detected patterns
- Provides groundwork for QR code data extraction

## Dependencies
- Python 3.x
- Required Packages:
  ```shell
  Pillow  # For image processing
  ```
- Project Modules:
  - `parse.py` (custom QR parsing logic)
  - `xmlpy.py` (custom SVG/XML builder)

## Usage
Run the script with an input QR image and output SVG path:
```shell
python main.py --input [input_image_path] --output [output_svg_path]
```

### Example:
```shell
python main.py --input qr.png --output analysis.svg
```

## Output
An SVG file containing:
1. Original QR code image
2. Gold rectangles highlighting timing patterns
3. Blue rectangles marking finder patterns
4. Transparent overlays for debug visualization

## Key Functionality
1. **Image Processing**  
   - Converts input image to RGB format
   - Uses block-based analysis with adjustable block size

2. **Pattern Detection**  
   - Run-length encoding (RLE) in both X and Y axes
   - Timing pattern identification
   - Finder pattern corner detection (TL, TR, BL positions)

3. **Visualization**  
   - SVG output with layered annotations
   - Color-coded pattern overlays
   - Coordinate system preservation

## Notes
- Ensure dependent modules (`parse.py`, `xmlpy.py`) are in the same directory
- Output SVG can be viewed in any modern web browser
- Designed as part of a larger QR decoding system (format patterns, data extraction)

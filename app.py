from flask import Flask, render_template, request, jsonify, send_file
import base64
import io
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont
from sklearn.cluster import KMeans
import colorsys
import webcolors
import json
import math
import random
from datetime import datetime
import tempfile
import os

app = Flask(__name__)

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex_color):
    """Convert hex to RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_cmyk(r, g, b):
    if (r, g, b) == (0, 0, 0):
        return (0, 0, 0, 100)
    r_prime = r / 255.0
    g_prime = g / 255.0
    b_prime = b / 255.0

    k = 1 - max(r_prime, g_prime, b_prime)
    c = (1 - r_prime - k) / (1 - k) if (1 - k) != 0 else 0
    m = (1 - g_prime - k) / (1 - k) if (1 - k) != 0 else 0
    y = (1 - b_prime - k) / (1 - k) if (1 - k) != 0 else 0

    return tuple(round(x * 100) for x in (c, m, y, k))

def rgb_to_hsl(r, g, b):
    """Convert RGB to HSL"""
    r, g, b = r/255.0, g/255.0, b/255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (round(h * 360), round(s * 100), round(l * 100))

def rgb_to_hsv(r, g, b):
    """Convert RGB to HSV"""
    r, g, b = r/255.0, g/255.0, b/255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (round(h * 360), round(s * 100), round(v * 100))

def hsl_to_rgb(h, s, l):
    """Convert HSL to RGB"""
    h = h / 360.0
    s = s / 100.0
    l = l / 100.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (round(r * 255), round(g * 255), round(b * 255))

def get_color_name(r, g, b):
    """Get the closest color name"""
    try:
        closest_name = webcolors.rgb_to_name((r, g, b))
        return closest_name
    except ValueError:
        min_colours = {}
        for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - r) ** 2
            gd = (g_c - g) ** 2
            bd = (b_c - b) ** 2
            min_colours[(rd + gd + bd)] = name
        return min_colours[min(min_colours.keys())]

def calculate_luminance(r, g, b):
    """Calculate relative luminance for accessibility"""
    def linearize(c):
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4
    
    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)
    
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

def get_contrast_ratio(color1, color2):
    """Calculate contrast ratio between two colors"""
    l1 = calculate_luminance(*color1)
    l2 = calculate_luminance(*color2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)

def get_contrast_color(r, g, b):
    """Get black or white text color for best contrast"""
    luminance = calculate_luminance(r, g, b)
    return '#000000' if luminance > 0.5 else '#ffffff'

def check_accessibility_compliance(color1, color2):
    """Check WCAG 2.1 accessibility compliance"""
    ratio = get_contrast_ratio(color1, color2)
    return {
        'ratio': round(ratio, 2),
        'aa_normal': ratio >= 4.5,
        'aa_large': ratio >= 3.0,
        'aaa_normal': ratio >= 7.0,
        'aaa_large': ratio >= 4.5
    }

def generate_color_harmony(base_color, harmony_type='complementary'):
    """Generate color harmonies based on color theory"""
    r, g, b = base_color
    h, s, l = rgb_to_hsl(r, g, b)
    
    harmonies = {
        'monochromatic': [
            hsl_to_rgb(h, max(s-30, 0), min(l+20, 100)),
            hsl_to_rgb(h, s, l),
            hsl_to_rgb(h, min(s+20, 100), max(l-20, 0)),
            hsl_to_rgb(h, max(s-10, 0), min(l+10, 100)),
            hsl_to_rgb(h, min(s+10, 100), max(l-10, 0))
        ],
        'analogous': [
            hsl_to_rgb((h-30) % 360, s, l),
            hsl_to_rgb((h-15) % 360, s, l),
            hsl_to_rgb(h, s, l),
            hsl_to_rgb((h+15) % 360, s, l),
            hsl_to_rgb((h+30) % 360, s, l)
        ],
        'complementary': [
            hsl_to_rgb(h, s, l),
            hsl_to_rgb((h+180) % 360, s, l),
            hsl_to_rgb(h, max(s-20, 0), min(l+15, 100)),
            hsl_to_rgb((h+180) % 360, max(s-20, 0), min(l+15, 100)),
            hsl_to_rgb(h, min(s+15, 100), max(l-15, 0))
        ],
        'triadic': [
            hsl_to_rgb(h, s, l),
            hsl_to_rgb((h+120) % 360, s, l),
            hsl_to_rgb((h+240) % 360, s, l),
            hsl_to_rgb(h, max(s-15, 0), min(l+10, 100)),
            hsl_to_rgb((h+120) % 360, max(s-15, 0), min(l+10, 100))
        ],
        'tetradic': [
            hsl_to_rgb(h, s, l),
            hsl_to_rgb((h+90) % 360, s, l),
            hsl_to_rgb((h+180) % 360, s, l),
            hsl_to_rgb((h+270) % 360, s, l),
            hsl_to_rgb(h, max(s-10, 0), min(l+10, 100))
        ],
        'split_complementary': [
            hsl_to_rgb(h, s, l),
            hsl_to_rgb((h+150) % 360, s, l),
            hsl_to_rgb((h+210) % 360, s, l),
            hsl_to_rgb(h, max(s-20, 0), min(l+20, 100)),
            hsl_to_rgb((h+180) % 360, max(s-30, 0), max(l-20, 0))
        ]
    }
    
    return harmonies.get(harmony_type, harmonies['complementary'])

def simulate_color_blindness(r, g, b, blindness_type='deuteranopia'):
    """Simulate different types of color blindness"""
    # Conversion matrices for different types of color blindness
    matrices = {
        'protanopia': [
            [0.567, 0.433, 0],
            [0.558, 0.442, 0],
            [0, 0.242, 0.758]
        ],
        'deuteranopia': [
            [0.625, 0.375, 0],
            [0.7, 0.3, 0],
            [0, 0.3, 0.7]
        ],
        'tritanopia': [
            [0.95, 0.05, 0],
            [0, 0.433, 0.567],
            [0, 0.475, 0.525]
        ],
        'achromatopsia': [
            [0.299, 0.587, 0.114],
            [0.299, 0.587, 0.114],
            [0.299, 0.587, 0.114]
        ]
    }
    
    if blindness_type not in matrices:
        return (r, g, b)
    
    matrix = matrices[blindness_type]
    
    # Normalize RGB values
    r_norm, g_norm, b_norm = r/255.0, g/255.0, b/255.0
    
    # Apply transformation matrix
    new_r = matrix[0][0] * r_norm + matrix[0][1] * g_norm + matrix[0][2] * b_norm
    new_g = matrix[1][0] * r_norm + matrix[1][1] * g_norm + matrix[1][2] * b_norm
    new_b = matrix[2][0] * r_norm + matrix[2][1] * g_norm + matrix[2][2] * b_norm
    
    # Denormalize and clamp
    return (
        max(0, min(255, round(new_r * 255))),
        max(0, min(255, round(new_g * 255))),
        max(0, min(255, round(new_b * 255)))
    )

def get_color_temperature(r, g, b):
    """Determine if color is warm or cool"""
    h, s, l = rgb_to_hsl(r, g, b)
    
    # Warm colors: red, orange, yellow (0-60, 300-360)
    # Cool colors: green, blue, purple (60-300)
    if (h >= 0 and h <= 60) or (h >= 300 and h <= 360):
        return 'warm'
    else:
        return 'cool'

def analyze_color_psychology(r, g, b):
    """Analyze color psychology and associations"""
    h, s, l = rgb_to_hsl(r, g, b)
    
    # Basic color psychology mapping
    psychology = {
        'dominant_trait': '',
        'emotions': [],
        'associations': [],
        'energy_level': '',
        'formality': ''
    }
    
    # Determine dominant hue
    if h < 15 or h >= 345:
        psychology['dominant_trait'] = 'passionate'
        psychology['emotions'] = ['energy', 'excitement', 'urgency']
        psychology['associations'] = ['love', 'danger', 'strength']
    elif h < 45:
        psychology['dominant_trait'] = 'optimistic'
        psychology['emotions'] = ['warmth', 'enthusiasm', 'creativity']
        psychology['associations'] = ['sunset', 'autumn', 'energy']
    elif h < 75:
        psychology['dominant_trait'] = 'cheerful'
        psychology['emotions'] = ['happiness', 'optimism', 'attention']
        psychology['associations'] = ['sun', 'gold', 'enlightenment']
    elif h < 165:
        psychology['dominant_trait'] = 'harmonious'
        psychology['emotions'] = ['balance', 'growth', 'freshness']
        psychology['associations'] = ['nature', 'money', 'health']
    elif h < 225:
        psychology['dominant_trait'] = 'trustworthy'
        psychology['emotions'] = ['calm', 'trust', 'stability']
        psychology['associations'] = ['sky', 'water', 'technology']
    elif h < 285:
        psychology['dominant_trait'] = 'mysterious'
        psychology['emotions'] = ['luxury', 'creativity', 'mystery']
        psychology['associations'] = ['royalty', 'magic', 'spirituality']
    else:
        psychology['dominant_trait'] = 'romantic'
        psychology['emotions'] = ['romance', 'femininity', 'playfulness']
        psychology['associations'] = ['flowers', 'sweetness', 'youth']
    
    # Energy level based on saturation and lightness
    if s > 70 and l > 50:
        psychology['energy_level'] = 'high'
    elif s > 40 and l > 30:
        psychology['energy_level'] = 'medium'
    else:
        psychology['energy_level'] = 'low'
    
    # Formality based on lightness and saturation
    if l < 30 or (s < 20 and l < 80):
        psychology['formality'] = 'formal'
    elif l > 80 or s < 30:
        psychology['formality'] = 'casual'
    else:
        psychology['formality'] = 'semi-formal'
    
    return psychology

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    data_url = request.form.get('cropped_image')
    num_colors = int(request.form.get('num_colors', 5))
    
    if num_colors < 2 or num_colors > 10:
        return jsonify({'error': 'Number of colors must be between 2 and 10.'}), 400
    
    if not data_url:
        return jsonify({'error': 'No image data received.'}), 400

    try:
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid base64 data.'}), 400

    try:
        image = Image.open(io.BytesIO(image_data))
        
        if len(image_data) > 10 * 1024 * 1024:
            return jsonify({'error': 'Image too large. Please use an image smaller than 10MB.'}), 400
        
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        
        max_size = 800 if max(image.size) > 2000 else 1500
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        width, height = image.size
        total_pixels = width * height

        img_array = np.array(image)
        h, w, _ = img_array.shape
        img_array = img_array.reshape((h * w, 3))

        kmeans = KMeans(n_clusters=num_colors, n_init=10, random_state=42, max_iter=300)
        kmeans.fit(img_array)
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_

        counts = np.bincount(labels)
        sorted_indices = np.argsort(-counts)

        colors_data = []
        for idx, cluster_idx in enumerate(sorted_indices):
            r, g, b = [int(x) for x in cluster_centers[cluster_idx]]
            pixel_count = counts[cluster_idx]
            percentage = round((pixel_count / total_pixels) * 100, 1)
            
            hex_color = rgb_to_hex(r, g, b)
            c, m, y, k = rgb_to_cmyk(r, g, b)
            h_hsl, s_hsl, l_hsl = rgb_to_hsl(r, g, b)
            h_hsv, s_hsv, v_hsv = rgb_to_hsv(r, g, b)
            color_name = get_color_name(r, g, b)
            contrast_color = get_contrast_color(r, g, b)
            luminance = round(calculate_luminance(r, g, b), 3)
            temperature = get_color_temperature(r, g, b)
            psychology = analyze_color_psychology(r, g, b)

            colors_data.append({
                'rank': idx + 1,
                'hex': hex_color,
                'rgb': f'rgb({r}, {g}, {b})',
                'rgb_values': [r, g, b],
                'cmyk': f'cmyk({c}%, {m}%, {y}%, {k}%)',
                'hsl': f'hsl({h_hsl}, {s_hsl}%, {l_hsl}%)',
                'hsv': f'hsv({h_hsv}, {s_hsv}%, {v_hsv}%)',
                'name': color_name,
                'percentage': percentage,
                'pixel_count': int(pixel_count),
                'contrast_color': contrast_color,
                'luminance': luminance,
                'temperature': temperature,
                'psychology': psychology
            })

        return jsonify({
            'colors': colors_data,
            'image_info': {
                'width': width,
                'height': height,
                'total_pixels': total_pixels
            }
        })

    except Exception as e:
        app.logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': f'Could not process image: {str(e)}'}), 400

@app.route('/single-pixel', methods=['POST'])
def single_pixel():
    """Get color information for a single pixel"""
    try:
        data_url = request.form.get('image_data')
        x = int(request.form.get('x'))
        y = int(request.form.get('y'))
        
        if not data_url:
            return jsonify({'error': 'No image data received.'}), 400

        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
        
        image = Image.open(io.BytesIO(image_data))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        
        try:
            r, g, b = image.getpixel((x, y))
        except IndexError:
            return jsonify({'error': 'Coordinates are outside image bounds.'}), 400
        
        hex_color = rgb_to_hex(r, g, b)
        c, m, y, k = rgb_to_cmyk(r, g, b)
        h, s, l = rgb_to_hsl(r, g, b)
        h_hsv, s_hsv, v_hsv = rgb_to_hsv(r, g, b)
        color_name = get_color_name(r, g, b)
        contrast_color = get_contrast_color(r, g, b)
        luminance = round(calculate_luminance(r, g, b), 3)
        temperature = get_color_temperature(r, g, b)
        psychology = analyze_color_psychology(r, g, b)
        
        return jsonify({
            'color': {
                'hex': hex_color,
                'rgb': f'rgb({r}, {g}, {b})',
                'rgb_values': [r, g, b],
                'cmyk': f'cmyk({c}%, {m}%, {y}%, {k}%)',
                'hsl': f'hsl({h}, {s}%, {l}%)',
                'hsv': f'hsv({h_hsv}, {s_hsv}%, {v_hsv}%)',
                'name': color_name,
                'contrast_color': contrast_color,
                'luminance': luminance,
                'temperature': temperature,
                'psychology': psychology,
                'coordinates': [x, y]
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting pixel color: {str(e)}")
        return jsonify({'error': f'Could not get pixel color: {str(e)}'}), 400

@app.route('/generate-harmony', methods=['POST'])
def generate_harmony():
    """Generate color harmonies based on a base color"""
    try:
        hex_color = request.form.get('base_color', '#ff0000')
        harmony_type = request.form.get('harmony_type', 'complementary')
        
        # Convert hex to RGB
        base_rgb = hex_to_rgb(hex_color)
        
        # Generate harmony
        harmony_colors = generate_color_harmony(base_rgb, harmony_type)
        
        colors_data = []
        for idx, (r, g, b) in enumerate(harmony_colors):
            hex_color = rgb_to_hex(r, g, b)
            color_name = get_color_name(r, g, b)
            c, m, y, k = rgb_to_cmyk(r, g, b)
            h, s, l = rgb_to_hsl(r, g, b)
            psychology = analyze_color_psychology(r, g, b)
            
            colors_data.append({
                'hex': hex_color,
                'rgb': f'rgb({r}, {g}, {b})',
                'rgb_values': [r, g, b],
                'cmyk': f'cmyk({c}%, {m}%, {y}%, {k}%)',
                'hsl': f'hsl({h}, {s}%, {l}%)',
                'name': color_name,
                'psychology': psychology
            })
        
        return jsonify({
            'harmony_type': harmony_type,
            'colors': colors_data
        })
        
    except Exception as e:
        app.logger.error(f"Error generating harmony: {str(e)}")
        return jsonify({'error': f'Could not generate harmony: {str(e)}'}), 400

@app.route('/accessibility-check', methods=['POST'])
def accessibility_check():
    """Check accessibility compliance for color combinations"""
    try:
        colors = request.json.get('colors', [])
        
        if len(colors) < 2:
            return jsonify({'error': 'At least 2 colors required for accessibility check.'}), 400
        
        results = []
        for i, color1 in enumerate(colors):
            for j, color2 in enumerate(colors):
                if i != j:
                    rgb1 = hex_to_rgb(color1)
                    rgb2 = hex_to_rgb(color2)
                    
                    compliance = check_accessibility_compliance(rgb1, rgb2)
                    
                    results.append({
                        'color1': color1,
                        'color2': color2,
                        'contrast_ratio': compliance['ratio'],
                        'wcag_aa_normal': compliance['aa_normal'],
                        'wcag_aa_large': compliance['aa_large'],
                        'wcag_aaa_normal': compliance['aaa_normal'],
                        'wcag_aaa_large': compliance['aaa_large']
                    })
        
        return jsonify({'accessibility_results': results})
        
    except Exception as e:
        app.logger.error(f"Error checking accessibility: {str(e)}")
        return jsonify({'error': f'Could not check accessibility: {str(e)}'}), 400

@app.route('/color-blindness', methods=['POST'])
def color_blindness_simulation():
    """Simulate color blindness for a palette"""
    try:
        colors = request.json.get('colors', [])
        blindness_types = ['protanopia', 'deuteranopia', 'tritanopia', 'achromatopsia']
        
        results = {}
        for blindness_type in blindness_types:
            simulated_colors = []
            for hex_color in colors:
                rgb = hex_to_rgb(hex_color)
                simulated_rgb = simulate_color_blindness(*rgb, blindness_type)
                simulated_hex = rgb_to_hex(*simulated_rgb)
                
                simulated_colors.append({
                    'original': hex_color,
                    'simulated': simulated_hex,
                    'simulated_rgb': simulated_rgb
                })
            
            results[blindness_type] = simulated_colors
        
        return jsonify({'simulations': results})
        
    except Exception as e:
        app.logger.error(f"Error simulating color blindness: {str(e)}")
        return jsonify({'error': f'Could not simulate color blindness: {str(e)}'}), 400

@app.route('/generate-mockup', methods=['POST'])
def generate_mockup():
    """Generate a visual mockup using the color palette"""
    try:
        colors = request.json.get('colors', [])
        mockup_type = request.json.get('mockup_type', 'website')
        
        if not colors:
            return jsonify({'error': 'No colors provided for mockup.'}), 400
        
        # Create a simple mockup image
        width, height = 800, 600
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        if mockup_type == 'website':
            # Generate a website mockup
            # Header
            header_color = hex_to_rgb(colors[0])
            draw.rectangle([0, 0, width, 80], fill=header_color)
            
            # Sidebar
            if len(colors) > 1:
                sidebar_color = hex_to_rgb(colors[1])
                draw.rectangle([0, 80, 200, height], fill=sidebar_color)
            
            # Main content area
            if len(colors) > 2:
                content_color = hex_to_rgb(colors[2])
                draw.rectangle([200, 80, width, height-60], fill=content_color)
            
            # Footer
            if len(colors) > 3:
                footer_color = hex_to_rgb(colors[3])
                draw.rectangle([0, height-60, width, height], fill=footer_color)
                
        elif mockup_type == 'logo':
            # Generate a logo mockup with color blocks
            block_width = width // len(colors)
            for i, color in enumerate(colors):
                color_rgb = hex_to_rgb(color)
                x1 = i * block_width
                x2 = (i + 1) * block_width if i < len(colors) - 1 else width
                draw.rectangle([x1, height//3, x2, 2*height//3], fill=color_rgb)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image.save(temp_file.name, 'PNG')
        
        # Convert to base64
        with open(temp_file.name, 'rb') as f:
            img_data = f.read()
            img_base64 = base64.b64encode(img_data).decode()
        
        # Clean up
        os.unlink(temp_file.name)
        
        return jsonify({
            'mockup_image': f'data:image/png;base64,{img_base64}',
            'mockup_type': mockup_type
        })
        
    except Exception as e:
        app.logger.error(f"Error generating mockup: {str(e)}")
        return jsonify({'error': f'Could not generate mockup: {str(e)}'}), 400

@app.route('/export-palette', methods=['POST'])
def export_palette():
    """Export palette in various formats"""
    try:
        colors = request.json.get('colors', [])
        export_format = request.json.get('format', 'json')
        palette_name = request.json.get('name', 'Custom Palette')
        
        if not colors:
            return jsonify({'error': 'No colors provided for export.'}), 400
        
        if export_format == 'ase':
            # Adobe Swatch Exchange format (simplified)
            return jsonify({'error': 'ASE format not yet implemented.'}), 400
            
        elif export_format == 'css':
            css_content = f"/* {palette_name} */\n:root {{\n"
            for i, color in enumerate(colors):
                css_content += f"  --color-{i+1}: {color};\n"
            css_content += "}\n"
            
            return jsonify({
                'content': css_content,
                'filename': f'{palette_name.lower().replace(" ", "-")}.css',
                'mime_type': 'text/css'
            })
            
        elif export_format == 'scss':
            scss_content = f"// {palette_name}\n"
            for i, color in enumerate(colors):
                scss_content += f"$color-{i+1}: {color};\n"
            
            return jsonify({
                'content': scss_content,
                'filename': f'{palette_name.lower().replace(" ", "-")}.scss',
                'mime_type': 'text/scss'
            })
            
        elif export_format == 'json':
            json_content = {
                'name': palette_name,
                'colors': colors,
                'created_at': datetime.now().isoformat(),
                'total_colors': len(colors)
            }
            
            return jsonify({
                'content': json.dumps(json_content, indent=2),
                'filename': f'{palette_name.lower().replace(" ", "-")}.json',
                'mime_type': 'application/json'
            })
            
        else:
            return jsonify({'error': 'Unsupported export format.'}), 400
            
    except Exception as e:
        app.logger.error(f"Error exporting palette: {str(e)}")
        return jsonify({'error': f'Could not export palette: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

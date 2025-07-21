from flask import Flask, render_template, request, jsonify
import base64
import io
import numpy as np
from PIL import Image, ImageOps
from sklearn.cluster import KMeans
import colorsys
import webcolors
import json

app = Flask(__name__)

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

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

def get_color_name(r, g, b):
    """Get the closest color name"""
    try:
        closest_name = webcolors.rgb_to_name((r, g, b))
        return closest_name
    except ValueError:
        # Find closest color name
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

def get_contrast_color(r, g, b):
    """Get black or white text color for best contrast"""
    luminance = calculate_luminance(r, g, b)
    return '#000000' if luminance > 0.5 else '#ffffff'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    data_url = request.form.get('cropped_image')
    num_colors = int(request.form.get('num_colors', 5))
    
    # Validate number of colors
    if num_colors < 2 or num_colors > 10:
        return jsonify({'error': 'Number of colors must be between 2 and 10.'}), 400
    
    if not data_url:
        return jsonify({'error': 'No image data received.'}), 400

    try:
        # Decode base64
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid base64 data.'}), 400

    try:
        # Open/transpose/convert
        image = Image.open(io.BytesIO(image_data))
        
        # Check file size
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({'error': 'Image too large. Please use an image smaller than 10MB.'}), 400
        
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        
        # More aggressive thumbnailing for very large images
        max_size = 800 if max(image.size) > 2000 else 1500
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Get image info
        width, height = image.size
        total_pixels = width * height

        # Flatten for K-Means
        img_array = np.array(image)
        h, w, _ = img_array.shape
        img_array = img_array.reshape((h * w, 3))

        # K-Means with better initialization
        kmeans = KMeans(n_clusters=num_colors, n_init=10, random_state=42, max_iter=300)
        kmeans.fit(img_array)
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_

        # Sort clusters by size
        counts = np.bincount(labels)
        sorted_indices = np.argsort(-counts)

        colors_data = []
        for idx, cluster_idx in enumerate(sorted_indices):
            r, g, b = [int(x) for x in cluster_centers[cluster_idx]]
            pixel_count = counts[cluster_idx]
            percentage = round((pixel_count / total_pixels) * 100, 1)
            
            # Get all color formats
            hex_color = rgb_to_hex(r, g, b)
            c, m, y, k = rgb_to_cmyk(r, g, b)
            h, s, l = rgb_to_hsl(r, g, b)
            h_hsv, s_hsv, v_hsv = rgb_to_hsv(r, g, b)
            color_name = get_color_name(r, g, b)
            contrast_color = get_contrast_color(r, g, b)
            luminance = round(calculate_luminance(r, g, b), 3)

            colors_data.append({
                'rank': idx + 1,
                'hex': hex_color,
                'rgb': f'rgb({r}, {g}, {b})',
                'rgb_values': [r, g, b],
                'cmyk': f'cmyk({c}%, {m}%, {y}%, {k}%)',
                'hsl': f'hsl({h}, {s}%, {l}%)',
                'hsv': f'hsv({h_hsv}, {s_hsv}%, {v_hsv}%)',
                'name': color_name,
                'percentage': percentage,
                'pixel_count': int(pixel_count),
                'contrast_color': contrast_color,
                'luminance': luminance
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

        # Decode base64
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
        
        image = Image.open(io.BytesIO(image_data))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        
        # Get pixel color
        try:
            r, g, b = image.getpixel((x, y))
        except IndexError:
            return jsonify({'error': 'Coordinates are outside image bounds.'}), 400
        
        # Get all color formats
        hex_color = rgb_to_hex(r, g, b)
        c, m, y, k = rgb_to_cmyk(r, g, b)
        h, s, l = rgb_to_hsl(r, g, b)
        h_hsv, s_hsv, v_hsv = rgb_to_hsv(r, g, b)
        color_name = get_color_name(r, g, b)
        contrast_color = get_contrast_color(r, g, b)
        luminance = round(calculate_luminance(r, g, b), 3)
        
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
                'coordinates': [x, y]
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting pixel color: {str(e)}")
        return jsonify({'error': f'Could not get pixel color: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

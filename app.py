from flask import Flask, render_template, request, jsonify
import base64
import io
import numpy as np
from PIL import Image, ImageOps
from sklearn.cluster import KMeans

app = Flask(__name__)

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def rgb_to_cmyk(r, g, b):
    if (r, g, b) == (0, 0, 0):
        # pure black
        return (0, 0, 0, 100)
    r_prime = r / 255.0
    g_prime = g / 255.0
    b_prime = b / 255.0

    k = 1 - max(r_prime, g_prime, b_prime)
    c = (1 - r_prime - k) / (1 - k) if (1 - k) != 0 else 0
    m = (1 - g_prime - k) / (1 - k) if (1 - k) != 0 else 0
    y = (1 - b_prime - k) / (1 - k) if (1 - k) != 0 else 0

    # Convert to percentage and round
    return tuple(round(x * 100) for x in (c, m, y, k))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    data_url = request.form.get('cropped_image')
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
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        image.thumbnail((1500, 1500))

        # Flatten for K-Means
        img_array = np.array(image)
        h, w, _ = img_array.shape
        img_array = img_array.reshape((h * w, 3))

        # K-Means
        kmeans = KMeans(n_clusters=5, n_init='auto')
        kmeans.fit(img_array)
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_

        # Sort clusters
        counts = np.bincount(labels)
        sorted_indices = np.argsort(-counts)
        top_n = 4
        sorted_indices = sorted_indices[:top_n]

        colors_data = []
        for idx in sorted_indices:
            r, g, b = [int(x) for x in cluster_centers[idx]]
            c, m, y, k = rgb_to_cmyk(r, g, b)

            colors_data.append({
                'hex': rgb_to_hex(r, g, b),
                'rgb': f'({r}, {g}, {b})',
                # Format CMYK nicely, e.g. (30%, 15%, 0%, 5%)
                'cmyk': f'({c}%, {m}%, {y}%, {k}%)'
            })

        return jsonify({'colors': colors_data})

    except Exception as e:
        return jsonify({'error': f'Could not process image. {str(e)}'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

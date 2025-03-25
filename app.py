from flask import Flask, render_template, request, jsonify
import base64
import io
import numpy as np
from PIL import Image, ImageOps
from sklearn.cluster import KMeans

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    data_url = request.form.get('cropped_image')
    if not data_url:
        return jsonify({'error': 'No image data received.'}), 400

    try:
        # Extract the base64 data
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid base64 data.'}), 400

    try:
        # Open, fix orientation, convert to RGB
        image = Image.open(io.BytesIO(image_data))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')

        # Optionally shrink large images
        image.thumbnail((1500, 1500))

        # Flatten for K-Means
        img_array = np.array(image)
        h, w, _ = img_array.shape
        img_array = img_array.reshape((h * w, 3))

        # K-Means with n_clusters=5 (adjust if you prefer)
        kmeans = KMeans(n_clusters=5, n_init='auto')
        kmeans.fit(img_array)
        cluster_centers = kmeans.cluster_centers_  # shape: (5, 3)
        labels = kmeans.labels_

        # Count occurrences of each cluster
        counts = np.bincount(labels)  # length: 5
        # Sort by frequency descending
        sorted_indices = np.argsort(-counts)

        # Keep the top 4 clusters
        top_n = 4
        sorted_indices = sorted_indices[:top_n]

        # Prepare an array of color data for JSON
        colors_data = []
        for idx in sorted_indices:
            # cluster_centers[idx] is [R, G, B] in floats
            r, g, b = [int(x) for x in cluster_centers[idx]]
            colors_data.append({
                'hex': rgb_to_hex(r, g, b),
                'rgb': f'({r}, {g}, {b})',
                'count': int(counts[idx])  # how many pixels in this cluster
            })

        # Return all 4 colors to the client
        return jsonify({'colors': colors_data})

    except Exception as e:
        return jsonify({'error': f'Could not process image. {str(e)}'}), 400


def rgb_to_hex(r, g, b):
    """Convert R, G, B in [0..255] to a HEX code."""
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

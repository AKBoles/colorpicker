from flask import Flask, render_template, request, jsonify
import base64
import io
import numpy as np
from PIL import Image, ImageOps
from sklearn.cluster import KMeans

app = Flask(__name__)

@app.route('/')
def index():
    """
    Render the main page with the Cropper.js UI.
    """
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """
    Receives a base64-encoded cropped image,
    corrects orientation, finds dominant color, returns as hex.
    """
    data_url = request.form.get('cropped_image')
    if not data_url:
        return jsonify({'error': 'No image data received.'}), 400

    # data:image/png;base64,iVBORw0K...
    try:
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid base64 data.'}), 400

    try:
        # Open the image in PIL
        image = Image.open(io.BytesIO(image_data))
        # Fix orientation from iPhones, etc.
        image = ImageOps.exif_transpose(image)
        # Convert to RGB
        image = image.convert('RGB')

        # Optionally resize in server code too, if needed:
        # This helps if user selected a big area but client-side didn't reduce enough.
        image.thumbnail((1500, 1500))  # keep it from exceeding 1500px in any dimension

        # Convert to NumPy array
        img_array = np.array(image)
        h, w, _ = img_array.shape
        # Flatten for K-Means
        img_array = img_array.reshape((h * w, 3))

        # K-Means to find the most prominent color
        kmeans = KMeans(n_clusters=5, n_init='auto')
        kmeans.fit(img_array)
        cluster_centers = kmeans.cluster_centers_
        cluster_labels = kmeans.labels_

        # Count how many pixels belong to each cluster
        counts = np.bincount(cluster_labels)

        # Most prominent color
        dominant_idx = np.argmax(counts)
        dominant_color = cluster_centers[dominant_idx]  # [R, G, B]

        # Convert float -> int
        r, g, b = [int(x) for x in dominant_color]
        # Convert to hex
        hex_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)

        return jsonify({'hex': hex_code})

    except Exception as e:
        return jsonify({'error': f'Could not process image. {str(e)}'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

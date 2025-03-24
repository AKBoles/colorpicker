from flask import Flask, render_template, request, jsonify
import base64
import io
import numpy as np
from PIL import Image
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
    Receives a base64-encoded cropped image via POST,
    extracts the most prominent color, and returns the hex code.
    """
    data_url = request.form.get('cropped_image')

    if not data_url:
        return jsonify({'error': 'No image data received.'}), 400

    # Data URL format: "data:image/png;base64,iVBORw0K..."
    # We need to split off the header part
    header, encoded = data_url.split(',', 1)

    # Decode the base64 string
    try:
        image_data = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid base64 data.'}), 400

    # Open the image in PIL
    image = Image.open(io.BytesIO(image_data)).convert('RGB')

    # Convert image to a small NumPy array to speed up clustering
    # (Optional: you can skip resizing if performance isn’t an issue)
    image = image.resize((150, 150))
    img_array = np.array(image)
    h, w, _ = img_array.shape
    img_array = img_array.reshape((h * w, 3))

    # Use K-Means to find the most prominent color
    # Set n_clusters to ~5 for a good balance:
    kmeans = KMeans(n_clusters=5, n_init='auto')
    kmeans.fit(img_array)
    cluster_centers = kmeans.cluster_centers_
    cluster_labels = kmeans.labels_

    # Count how many pixels belong to each cluster
    counts = np.bincount(cluster_labels)

    # The cluster with the most points is our "dominant" color
    dominant_idx = np.argmax(counts)
    dominant_color = cluster_centers[dominant_idx]  # [R, G, B]

    # Round the color values and convert to int
    r, g, b = [int(x) for x in dominant_color]

    # Convert to hex
    hex_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)

    return jsonify({'hex': hex_code})

if __name__ == '__main__':
    # When running locally, do "python app.py"
    app.run(host='0.0.0.0', port=5000, debug=True)

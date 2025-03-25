from flask import Flask, render_template, request, jsonify
import base64
import io
import numpy as np
from PIL import Image, ImageOps
from sklearn.cluster import KMeans
import colorsys

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
        header, encoded = data_url.split(',', 1)
        image_data = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Invalid base64 data.'}), 400

    try:
        image = Image.open(io.BytesIO(image_data))
        image = ImageOps.exif_transpose(image)
        image = image.convert('RGB')
        image.thumbnail((1500, 1500))  # Prevent super-large images

        img_array = np.array(image)
        h, w, _ = img_array.shape
        img_array = img_array.reshape((h * w, 3))

        kmeans = KMeans(n_clusters=5, n_init='auto')
        kmeans.fit(img_array)
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_

        counts = np.bincount(labels)
        dominant_idx = np.argmax(counts)
        dominant_color = cluster_centers[dominant_idx]  # [R, G, B]
        r, g, b = [int(x) for x in dominant_color]

        # Convert to different color spaces
        hex_code = rgb_to_hex(r, g, b)
        c, m, y, k = rgb_to_cmyk(r, g, b)
        h_hsl, s_hsl, l_hsl = rgb_to_hsl(r, g, b)

        return jsonify({
            'hex': hex_code,
            'rgb': f'({r}, {g}, {b})',
            'cmyk': f'({c:.0f}, {m:.0f}, {y:.0f}, {k:.0f})',
            'hsl': f'({h_hsl:.0f}°, {s_hsl:.0f}%, {l_hsl:.0f}%)'
        })

    except Exception as e:
        return jsonify({'error': f'Could not process image. {str(e)}'}), 400


def rgb_to_hex(r, g, b):
    """Return a HEX color string from R, G, B in [0..255]."""
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def rgb_to_cmyk(r, g, b):
    """
    Convert (r,g,b) in [0..255] to (c,m,y,k) in [0..100].
    Basic formula: https://www.rapidtables.com/convert/color/rgb-to-cmyk.html
    """
    if (r, g, b) == (0, 0, 0):
        # Black
        return (0, 0, 0, 100)

    # Convert to 0..1
    r_f = r / 255.0
    g_f = g / 255.0
    b_f = b / 255.0

    k = 1 - max(r_f, g_f, b_f)
    c = (1 - r_f - k) / (1 - k) if (1 - k) != 0 else 0
    m = (1 - g_f - k) / (1 - k) if (1 - k) != 0 else 0
    y = (1 - b_f - k) / (1 - k) if (1 - k) != 0 else 0

    # Convert to percentages
    return (c * 100, m * 100, y * 100, k * 100)

def rgb_to_hsl(r, g, b):
    """
    Convert (r,g,b) in [0..255] to (H,S,L) in degrees/percent.
    Using Python's colorsys, which uses (R,G,B) in [0..1].
    """
    r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(r_f, g_f, b_f)
    # colorsys returns H in [0..1] (as a fraction of a circle),
    # L and S in [0..1].
    h_deg = h * 360
    s_perc = s * 100
    l_perc = l * 100
    return (h_deg, s_perc, l_perc)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

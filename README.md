# Advanced Color Picker & Palette Analyzer

A sophisticated web application for **image color analysis** with advanced features including crop-based analysis, single-pixel color picking, and comprehensive color format support. Built with **Flask**, **Cropper.js**, **NumPy**, **scikit-learn**, and **Pillow**.

![Color Picker Demo](./images/example1.jpg)

## 🌟 Features

### **Core Functionality**
- **Multi-Cluster Analysis**: Uses **K-Means clustering** to identify 2-10 dominant colors
- **Dual Analysis Modes**: 
  - **Crop Mode**: Analyze colors in a selected region
  - **Pixel Picker Mode**: Get detailed color info for individual pixels
- **Multiple Color Formats**: HEX, RGB, CMYK, HSL, HSV support
- **Color Name Identification**: Automatic color name detection using CSS3 color names
- **Accessibility Features**: Luminance calculation and contrast color determination

### **Advanced UI/UX**
- **Modern Design**: Glassmorphism effects with gradient backgrounds
- **Drag & Drop Support**: Upload images by dragging them onto the interface
- **Responsive Layout**: Mobile-friendly grid system
- **Real-time Controls**: Adjustable color count with live slider feedback
- **Loading States**: Progress indicators for better user experience
- **Error Handling**: Comprehensive error messages with auto-dismiss

### **Professional Features**
- **Orientation Correction**: Automatic EXIF orientation handling
- **Image Optimization**: Smart thumbnailing for large images (10MB limit)
- **Copy to Clipboard**: One-click copying of individual color values
- **Palette Export**: Download color palettes as JSON files
- **Bulk Operations**: Copy all colors at once
- **Image Information**: Display dimensions and pixel count

### **Technical Improvements**
- **Better Algorithm**: Enhanced K-means with improved initialization
- **Performance Optimized**: Faster processing with smart image resizing
- **Memory Efficient**: In-memory processing without disk storage
- **Error Recovery**: Graceful handling of invalid inputs
- **Modern Dependencies**: Updated to latest compatible library versions

---

## 🎨 Color Information Provided

For each color, the application provides:

- **HEX Code** (e.g., `#ff6b35`)
- **RGB Values** (e.g., `rgb(255, 107, 53)`)
- **CMYK Values** (e.g., `cmyk(0%, 58%, 79%, 0%)`)
- **HSL Values** (e.g., `hsl(16, 100%, 60%)`)
- **HSV Values** (e.g., `hsv(16, 79%, 100%)`)
- **Color Name** (e.g., "OrangeRed")
- **Percentage Coverage** in the analyzed area
- **Pixel Count** and total occurrences
- **Luminance Value** for accessibility
- **Optimal Contrast Color** (black or white text)

---

## 🚀 Quick Start

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/color-picker.git
   cd color-picker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   ```
   http://localhost:5000
   ```

### **Docker Installation** (Optional)
```bash
docker build -t color-picker .
docker run -p 5000:5000 color-picker
```

---

## 📱 How to Use

### **Crop Mode** (Default)
1. **Upload Image**: Click the upload area or drag & drop an image file
2. **Configure Settings**: Adjust the number of colors (2-10) using the slider
3. **Crop Region**: Use the cropping tool to select your area of interest
4. **Analyze**: Click "Analyze Colors" to extract the color palette
5. **Explore Results**: View detailed color information and copy values
6. **Export**: Download the palette or copy all colors to clipboard

### **Pixel Picker Mode**
1. **Switch Mode**: Click the "Pixel Picker" button
2. **Upload Image**: Upload your image as usual
3. **Click Pixels**: Click anywhere on the image to get color information
4. **View Details**: See comprehensive color data for the selected pixel

---

## 🔧 Configuration Options

- **Color Count**: 2-10 colors (adjustable via slider)
- **Image Size Limit**: 10MB maximum
- **Output Formats**: HEX, RGB, CMYK, HSL, HSV
- **Export Formats**: JSON palette files

---

## 🌐 Browser Support

- **Modern Browsers**: Chrome 88+, Firefox 85+, Safari 14+, Edge 88+
- **Mobile Support**: iOS Safari 14+, Android Chrome 88+
- **Features Used**: File API, Canvas API, Fetch API, CSS Grid, CSS Custom Properties

---

## 🎯 Use Cases

- **Web Design**: Extract color palettes from inspiration images
- **Brand Development**: Analyze competitor color schemes
- **Art & Photography**: Study color composition in artwork
- **Print Design**: Get CMYK values for print production
- **Accessibility**: Check color contrast and luminance values
- **Data Visualization**: Create color schemes from real-world data

---

## 🔍 Technical Details

### **Algorithm**
- **K-Means Clustering**: Scikit-learn implementation with optimized parameters
- **Color Space**: RGB color space with CIELAB perceptual improvements
- **Initialization**: K-means++ for better cluster starting points
- **Convergence**: Maximum 300 iterations with random state seeding

### **Image Processing**
- **Format Support**: JPEG, PNG, WebP, GIF, BMP, TIFF
- **EXIF Handling**: Automatic orientation correction
- **Compression**: Smart thumbnailing with LANCZOS resampling
- **Memory Management**: Streaming processing without temporary files

### **Performance**
- **Client-Side**: Cropper.js for responsive image manipulation
- **Server-Side**: Optimized NumPy operations
- **Network**: Base64 encoding for secure image transfer
- **Caching**: Browser caching for static assets

---

## 📦 Dependencies

```
Flask>=3.1.0          # Web framework
Werkzeug>=3.1.0       # WSGI utilities
Pillow>=11.0.0        # Image processing
scikit-learn>=1.7.0   # Machine learning (K-means)
numpy>=2.3.0          # Numerical computing
webcolors>=24.8.0     # Color name identification
```

**Frontend Libraries:**
- Cropper.js 1.5.12 (Image cropping)
- Font Awesome 6.0.0 (Icons)

---

## 🚀 Deployment

### **Render.com**
```bash
# Build Command
pip install -r requirements.txt

# Start Command
python app.py
```

### **Heroku**
```bash
heroku create your-color-picker
git push heroku main
```

### **Railway**
```bash
railway deploy
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Cropper.js** for the excellent image cropping functionality
- **Scikit-learn** for the robust K-means implementation
- **Font Awesome** for the beautiful icons
- **Pillow** for comprehensive image processing capabilities

---

## 📸 Screenshots

### Main Interface
![Main Interface](./images/main-interface.png)

### Color Analysis Results
![Color Results](./images/color-results.png)

### Pixel Picker Mode
![Pixel Picker](./images/pixel-picker.png)

---

Made with ❤️ for designers, developers, and color enthusiasts!

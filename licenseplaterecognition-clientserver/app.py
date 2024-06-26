from flask import Flask, request, render_template, redirect, flash
import os
import cv2
import pytesseract

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def detect_license_plate(image):
    # Converting image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Applying edge detection
    edges = cv2.Canny(gray, 100, 200)
    # Finding contours in the edge-detected image
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour
    
    # Getting the bounding box of the largest contour
    x, y, w, h = cv2.boundingRect(max_contour)
    # Extracting the license plate region from the original image
    license_plate = gray[y:y+h, x:x+w]
    
    # Using Tesseract OCR to perform character recognition
    detected_plate_text = pytesseract.image_to_string(license_plate,lang='eng',  config='--psm 11')
    
    return detected_plate_text, (x, y, w, h)

@app.route('/', methods=['GET', 'POST'])
def index():
    detected_plate = None
    filename = None
    license_plate_region = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            # Save the uploaded file
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image = cv2.imread(file_path)
            # Detect license plate
            detected_plate_text, license_plate_region = detect_license_plate(image)
            if license_plate_region:
                x, y, w, h = license_plate_region
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Save the modified image with rectangle drawn
                cv2.imwrite(file_path, image)
            detected_plate = detected_plate_text
    return render_template('index.html', filename=filename, detected_plate=detected_plate, license_plate_region=license_plate_region)

if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, request, render_template, redirect, flash
import os
import cv2
import pytesseract

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def detect_license_plate(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    edges = cv2.Canny(gray, 100, 200)
    
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour
    
    x, y, w, h = cv2.boundingRect(max_contour)
    
    license_plate = gray[y:y+h, x:x+w]
    
    detected_plate = pytesseract.image_to_string(license_plate, config='--psm 8')
    
    return detected_plate

@app.route('/', methods=['GET', 'POST'])
def index():
    detected_plate = None
    filename = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image = cv2.imread(file_path)
            detected_plate = detect_license_plate(image)
    return render_template('index.html', filename=filename, detected_plate=detected_plate)

if __name__ == '__main__':
    app.run(debug=True)
# import os
# from flask import Flask, request, render_template, redirect, flash
# import cv2
# import xml.etree.ElementTree as ET
# import numpy as np
# import pytesseract

# app = Flask(__name__)
# app.secret_key = 'super_secret_key'

# UPLOAD_FOLDER = 'static/uploads'
# PROCESSED_FOLDER = 'static/processed'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# # Set up Tesseract path
# pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # Update this to your Tesseract path

# def read_image_and_annotation(image_path, annotation_path):
#     # Read image
#     image = cv2.imread(image_path)
#     # Convert to RGB
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
#     # Read XML annotation for bounding box
#     tree = ET.parse(annotation_path)
#     root = tree.getroot()
#     xmin, ymin, xmax, ymax = 0, 0, 0, 0
#     for member in root.findall('object'):
#         xmin = int(member[4][0].text)
#         ymin = int(member[4][1].text)
#         xmax = int(member[4][2].text)
#         ymax = int(member[4][3].text)
    
#     # Crop to the bounding box
#     plate_image = image[ymin:ymax, xmin:xmax]
#     return image, plate_image

# def preprocess_for_ocr(image):
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
#     # Noise reduction and binarization
#     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#     # Further noise reduction
#     denoised = cv2.fastNlMeansDenoising(binary, h=10)
#     return denoised

# def extract_text(image):
#     # Use Tesseract to do OCR on the image
#     text = pytesseract.image_to_string(image, lang='eng', config='--psm 9')
#     return text.strip()

# # Handle the form submission
# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         if 'file' not in request.files or 'annotation' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         image_file = request.files['file']
#         annotation_file = request.files['annotation']
#         if image_file.filename == '' or annotation_file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if image_file and annotation_file:
#             # Save the uploaded files
#             image_filename = image_file.filename
#             annotation_filename = annotation_file.filename
#             image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
#             annotation_path = os.path.join(app.config['UPLOAD_FOLDER'], annotation_filename)
#             image_file.save(image_path)
#             annotation_file.save(annotation_path)
#             # Read the uploaded files
#             original_image, plate_image = read_image_and_annotation(image_path, annotation_path)
#             # Process the images and extract text
#             preprocessed_image = preprocess_for_ocr(plate_image)
#             processed_image_filename = os.path.splitext(image_filename)[0] + '_processed.jpg'
#             processed_image_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_image_filename)
#             cv2.imwrite(processed_image_path, preprocessed_image)
#             text = extract_text(preprocessed_image)
#             # Render the result template with extracted text
#             return render_template('result.html', original_image=image_filename, processed_image=processed_image_filename, text=text)
#     return render_template('index.html')

# if __name__ == '__main__':
#     app.run(debug=True)



import os
from flask import Flask, request, render_template, redirect, flash
import cv2
import xml.etree.ElementTree as ET
import numpy as np
import pytesseract

app = Flask(__name__)
app.secret_key = 'super_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ANNOTATION_FOLDER = 'static/annotations'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ANNOTATION_FOLDER'] = ANNOTATION_FOLDER

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

def read_annotation(annotation_path):
    tree = ET.parse(annotation_path)
    root = tree.getroot()
    xmin, ymin, xmax, ymax = 0, 0, 0, 0
    for member in root.findall('object'):
        xmin = int(member[4][0].text)
        ymin = int(member[4][1].text)
        xmax = int(member[4][2].text)
        ymax = int(member[4][3].text)
    return xmin, ymin, xmax, ymax

def preprocess_for_ocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.fastNlMeansDenoising(binary, h=10)
    return denoised

def extract_text(image):
    text = pytesseract.image_to_string(image, lang='eng', config='--psm 8')
    return text.strip()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        image_file = request.files['file']
        if image_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if image_file:
            # Save the uploaded image
            image_filename = image_file.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
            
            xml_filename = os.path.splitext(image_filename)[0] + '.xml'
            annotation_path = os.path.join(app.config['ANNOTATION_FOLDER'], xml_filename)
            
            if os.path.exists(annotation_path):
                image = cv2.imread(image_path)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                # Read the corresponding XML annotation
                xmin, ymin, xmax, ymax = read_annotation(annotation_path)
                # Crop the plate from the image based on the annotation
                plate_image = image[ymin:ymax, xmin:xmax]
                
                # Preprocess the plate image for OCR
                preprocessed_image = preprocess_for_ocr(plate_image)
                
                # Extract text from the plate image
                text = extract_text(preprocessed_image)
                
                # Render the result template with extracted text
                return render_template('result.html', original_image=image_filename, text=text)
            else:
                flash('No corresponding XML annotation found')
                return redirect(request.url)
    return render_template('index.html')

@app.route('/video')
def video():
    return render_template('/video.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", PORT=8080, debug=True )






# flask run --port=8080
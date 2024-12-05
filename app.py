from flask import Flask, render_template, request, redirect, url_for
import os
import cv2
from google.cloud import vision
from PIL import Image
import io

app = Flask(__name__)

# Set the path for uploading images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Google Vision Client Setup
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'your-google-credentials.json'  # Add your Google Vision API credentials

def detect_and_crop_faces(image_path):
    # Load the image using OpenCV
    img = cv2.imread(image_path)
    
    # Convert to grayscale (required for face detection)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Load OpenCV's pre-trained face detector (Haar Cascade)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # If no faces are detected, return an empty list
    if len(faces) == 0:
        return []

    # List to hold cropped face images
    cropped_faces = []
    
    # Crop the faces from the image
    for (x, y, w, h) in faces:
        face_img = img[y:y+h, x:x+w]
        pil_image = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
        cropped_faces.append(pil_image)

    return cropped_faces

def reverse_image_search(image_path):
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)

    response = client.web_detection(image=image)
    annotations = response.web_detection

    if annotations.web_entities:
        return [(entity.description, entity.score) for entity in annotations.web_entities]
    else:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    # Save the uploaded file
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(image_path)

    # Detect and crop faces
    cropped_faces = detect_and_crop_faces(image_path)

    if not cropped_faces:
        return "No faces detected. Try again with a clearer image."

    # Save the first cropped face and perform reverse image search
    cropped_faces[0].save("cropped_face.jpg")
    search_results = reverse_image_search("cropped_face.jpg")

    return render_template('results.html', search_results=search_results, image_url="cropped_face.jpg")

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for
import cv2
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

app = Flask(__name__)

# Set the default username and password
default_username = 'admin'
default_password = '12345'

# Define the login route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == default_username and password == default_password:
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error=True)
    else:
        return render_template('login.html', error=False)

# Define the home route
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        student_name = request.form['student_name']
        reg_no = request.form['reg_no']
        department = request.form['department']
        staff_incharge = request.form['staff_incharge']
        return render_template('start.html')
    else:
        return render_template('home.html')


@app.route('/run_opencv', methods=['POST'])
def run_opencv():
    reg_no = request.form['reg_no']
    dir_name = os.path.join('captured_images', reg_no)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    cap = cv2.VideoCapture(0)
    count = 1

    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            r'\haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Add count to the image
        cv2.putText(frame, f'Count: {count}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow('frame', frame)
        img_name = os.path.join(dir_name, f'image_{count}.png')
        cv2.imwrite(img_name, frame)

        count += 1

        if count == 50:
            cap.release()
            cv2.destroyAllWindows()
            break

        if cv2.waitKey(100) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break

    # Upload all the images to Azure Blob Storage
    connect_str = 'Your Azure Connection String'
    container_name = 'images'
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)

    for file_name in os.listdir(dir_name):
        blob_client = container_client.get_blob_client(os.path.join(reg_no, os.path.basename(file_name)))
        with open(os.path.join(dir_name, file_name), "rb") as data:
            blob_client.upload_blob(data)

    return render_template('registration_success.html')


if __name__ == '__main__':
    app.run(debug=True)
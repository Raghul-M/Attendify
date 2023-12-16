import numpy as np
import cv2
import pickle
import pandas as pd
import os.path
from datetime import datetime
from azure.storage.blob import BlobServiceClient
import time

# Set the connection string to your Azure Storage account
connect_str = "Your Azure Connection string"

# Set the container name and the file names to download
container_name = "recognizer-files"
labels_filename = "labels.pickle"
trainer_filename = "trainner.yml"

# Create a BlobServiceClient object
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Get a reference to the container
container_client = blob_service_client.get_container_client(container_name)

# Download the labels.pickle file
labels_blob_client = container_client.get_blob_client(labels_filename)
with open(labels_filename, "wb") as f:
    data = labels_blob_client.download_blob().readall()
    f.write(data)

# Download the trainner.yml file
trainer_blob_client = container_client.get_blob_client(trainer_filename)
with open(trainer_filename, "wb") as f:
    data = trainer_blob_client.download_blob().readall()
    f.write(data)


face_casecade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainner.yml")

labels = {"persons_name": 1}
with open("labels.pickle", "rb") as f:
    labels = pickle.load(f)
    labels = {v: k for k, v in labels.items()}

attendance_records = []
face_detected = False

cap = cv2.VideoCapture(0)
start_time = time.time()
while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_casecade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5)
    for (x, y, w, h) in faces:
        roi_color = frame[y:y + h, x:x + w]
        roi_gray = gray[y:y + h, x:x + w]

        id_, conf = recognizer.predict(roi_gray)

        if conf < 35:
            name = "unknown"
        else:
            name = labels[id_]
            if not face_detected:
                attendance_records.append((name, "present", datetime.now()))
                face_detected = True

        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (255, 255, 255)
        stroke = 2
        cv2.putText(frame, name, (x, y), font, 1, color, stroke, cv2.LINE_AA)

        color = (255, 0, 0)
        stroke = 2
        end_cord_x = x + w
        end_cord_y = y + h
        cv2.rectangle(frame, (x, y), (end_cord_x, end_cord_y), color, stroke)

    cv2.imshow('frame', frame)

    if face_detected and (time.time() - start_time) >= 5:
        break

    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# create attendance dataframe and write


# create attendance dataframe and write to excel file
if len(attendance_records) > 0:
    date_string = datetime.now().strftime("%Y-%m-%d")
    file_name = f"attendance_records_{date_string}.xlsx"
    df = pd.DataFrame(attendance_records, columns=["Register Number", "Attendance", "Time"])
    df.to_excel(file_name, index=False)
    print(f"Attendance record has been created and saved as {file_name}.")

    # Set the connection string to your Azure Storage account
    #connect_str = "DefaultEndpointsProtocol=https;AccountName=attendify;AccountKey=LIztLfHsAQxAS4ViVRATWSIzxm/sVQ148L+6ZG/DlHAXia1Ck59oLQY6k9EkwyFshr3gKELsZKjn+ASt9h/tSQ==;EndpointSuffix=core.windows.net"

    # Set the container name
    container_name = "attendance-files"

    # Create a BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)

    # Upload the Excel file to the container
    with open(file_name, "rb") as data:
        container_client.upload_blob(name=file_name, data=data, overwrite=True)

    print(f"{file_name} has been uploaded to the {container_name} container.")
else:
    print("No faces were recognized.")


    # send the file to the specified email address



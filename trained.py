import os
import io
import uuid
import json
import requests
import logging
import cv2
import numpy as np
from PIL import Image
import pickle
from azure.storage.blob import BlobServiceClient, BlobClient

# Initialize Azure Blob Storage client
connection_string = 'Your Azure Connection String'
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Initialize local directories
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#image_dir = os.path.join(BASE_DIR, "captured_images")

# Load face cascade classifier and create face recognizer
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Initialize label and training data lists
current_id = 0
label_ids = {}
y_labels = []
x_train = []

# Download images from the Azure Blob Storage container and process them
container_name = 'images'
for blob in blob_service_client.get_container_client(container_name).list_blobs():
    if blob.name.endswith("png") or blob.name.endswith("jpg"):
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob.name)
        image_data = blob_client.download_blob().readall()
        image_stream = io.BytesIO(image_data)
        pil_image = Image.open(image_stream).convert("L")
        size = (550, 550)
        final_image = pil_image.resize(size, Image.LANCZOS)
        image_array = np.array(final_image, "uint8")
        faces = face_cascade.detectMultiScale(image_array, scaleFactor=1.5, minNeighbors=5)
        label = os.path.basename(os.path.dirname(blob.name)).replace(" ", "-")

        if not label in label_ids:
            label_ids[label] = current_id
            current_id += 1
            id_ = label_ids[label]

        for (x, y, w, h) in faces:
            roi = image_array[y:y+h, x:x+w]
            x_train.append(roi)
            y_labels.append(id_)

# Save the label IDs to a pickle file
with open("labels.pickle", "wb") as f:
    pickle.dump(label_ids, f)

# Train the recognizer and save it to a YAML file
recognizer.train(x_train, np.array(y_labels))
recognizer.save("trainner.yml")

# Upload the trained data to a separate container in the Azure Blob Storage
labels_container_name = 'recognizer-files'
trainner_container_name = 'recognizer-files'
with open("labels.pickle", "rb") as f:
    blob_client = blob_service_client.get_blob_client(container=labels_container_name, blob="labels.pickle")
    blob_client.upload_blob(f.read(), overwrite=True)
with open("trainner.yml", "rb") as f:
    blob_client = blob_service_client.get_blob_client(container=trainner_container_name, blob="trainner.yml")
    blob_client.upload_blob(f.read(), overwrite=True)

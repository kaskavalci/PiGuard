#!/usr/bin/python

import face_recognition
import cv2
import numpy as np
from os import listdir
from os.path import join
from os import environ
import boto3
import uuid
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

AWS_ACCESS_KEY_ID = environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = environ['AWS_SECRET_ACCESS_KEY']
AWS_REGION = 'eu-west-1'
AWS_S3_BUCKET = 'unrecognized-faces'


class Recognizer():
    # Initialize some variables
    known_images_encoding = []
    names = []

    def __init__(self):
        # Load known pictures
        known_images_path = "known_images"

        for f in listdir(known_images_path):
            print f
            self.names.append(f)
            image = face_recognition.load_image_file(join(known_images_path, f))
            self.known_images_encoding.append(face_recognition.face_encodings(image)[0])

    def upload(self, image):
        filename = str(uuid.uuid4()) + ".jpg"
        path = "unrecognized/" + filename
        cv2.imwrite(path, image)

        # Create an S3 client
        s3 = boto3.client('s3',
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=AWS_REGION)

        # Uploads the given file using a managed uploader, which will split up large
        # files automatically and upload parts in parallel.
        print "uploading file " + filename + " to s3 now"
        s3.upload_file(path, AWS_S3_BUCKET, filename)

    def recognize(self, frame, small_frame):
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            match = face_recognition.compare_faces(self.known_images_encoding, face_encoding)
            name = "Unknown"

            print match
            found = False
            for i, m in enumerate(match):
                if m:
                    name = self.names[i]
                    found = True
            if not found:
                self.upload(frame)

            face_names.append(name)

        return face_names


class PUTHandler(BaseHTTPRequestHandler):
    recognizer = None

    def do_PUT(self):
        print self.headers
        if 'Content-Type' not in self.headers or self.headers['Content-Type'] not in ["image/jpeg", "image/jpg"]:
            print "we only accept image/jpeg types"
            self.send_response(500)
            return
        length = int(self.headers['Content-Length'])
        d = self.rfile.read(length)
        with open('image.jpg', 'wb') as fh:
            fh.write(d)
        content = cv2.imread('image.jpg')
        names = self.recognizer.recognize(content, content)
        print names
        self.send_response(204)


def run_on(addr, port):
    print("Starting a server on port %s:%i" % (addr, port))
    server_address = (addr, port)
    PUTHandler.recognizer = Recognizer()
    httpd = HTTPServer(server_address, PUTHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    run_on('localhost', 8080)

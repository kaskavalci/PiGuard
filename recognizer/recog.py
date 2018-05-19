#!/usr/bin/python

import face_recognition
import cv2
from os import listdir
from os import path, makedirs
from os import getenv
from os import remove
from os import rename
import boto3
import uuid
import socket
import time
import datetime
import argparse
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# AWS Credentials
AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = getenv('AWS_DEFAULT_REGION', 'eu-west-1')

# Path variables
known_faces_dir = 'known_images'
unknown = 'unknown'
images_dir = 'images'

class Recognizer():
    _args = None
    # Initialize some variables
    known_images_encoding = []
    names = []
    _table = None

    def __init__(self, args):
        self._args = args
        self._table = boto3.resource('dynamodb', region_name=AWS_REGION).Table(args.table)
        # Load known pictures
        known_images_path = known_faces_dir
        unknown_dir = path.join(images_dir, unknown)
        if not path.exists(unknown_dir):
            makedirs(unknown_dir)

        for f in listdir(known_images_path):
            name = f[:len(f)-4]
            print name
            self.names.append(name)
            image = face_recognition.load_image_file(path.join(known_images_path, f))
            self.known_images_encoding.append(face_recognition.face_encodings(image)[0])
            image_dir = path.join(images_dir, name)
            if not path.exists(image_dir):
                makedirs(image_dir)

    def upload(self, filename, filepath, image):
        # Create an S3 client
        s3 = boto3.client('s3',
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=AWS_REGION)

        # Uploads the given file using a managed uploader, which will split up large
        # files automatically and upload parts in parallel.
        print ("uploading file %s at %s to s3 bucket %s" %
               (filename, filepath, self._args.s3_bucket))
        s3.upload_file(filepath, self._args.s3_bucket, filename)

    def recognize(self, image_name, frame, small_frame):
        start = time.time()
        # Find all the faces and face encodings in the current frame of video
        face_encodings = face_recognition.face_encodings(small_frame)

        recognized_face = unknown
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            match = face_recognition.compare_faces(self.known_images_encoding, face_encoding)

            print match
            for i, m in enumerate(match):
                if m:
                    recognized_face = self.names[i]
            if recognized_face != unknown:
                break
            # face_names.append(name)

        # move to recognized or unknown folder
        image_path = path.join(images_dir, recognized_face, image_name)
        rename(image_name, image_path)
        # end of algorithm. no need to track uploading time
        elapsed = str(time.time() - start)

        # upload only if we cannot recognize the face
        if recognized_face == unknown and self._args.upload:
            thread = Thread(target=self.upload, args=(image_name, image_path, frame))
            thread.start()

        print ('elapsed time %s' % elapsed)

        table_put_response = self._table.put_item(
            Item={
                'filename': image_name,
                'result': recognized_face,
                'created': str(datetime.datetime.utcnow()),
                'duration': elapsed
            }
        )
        return recognized_face

class PUTHandler(BaseHTTPRequestHandler):
    recognizer = None
    args = None

    def do_PUT(self):
        if 'Content-Type' not in self.headers or self.headers['Content-Type'] not in ["image/jpeg", "image/jpg"]:
            print "we only accept image/jpeg types"
            self.send_response(500)
            return
        length = int(self.headers['Content-Length'])
        self.send_response(204) # Return early response
        image_name = str(uuid.uuid4()) + ".jpg"
        if 'Filename' in self.headers:
            image_name = self.headers['Filename']
        d = self.rfile.read(length)
        with open(image_name, 'wb') as fh:
            fh.write(d)
        content = cv2.imread(image_name)
        names = self.recognizer.recognize(image_name, content, content)
        print names


def run_on(addr, port, args):
    print("Starting a server on port %s:%i" % (addr, port))
    server_address = (addr, port)
    PUTHandler.recognizer = Recognizer(args)
    PUTHandler.args = args
    httpd = HTTPServer(server_address, PUTHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Tracker')
    parser.add_argument('--upload', action='store_true', dest='upload', default=False)
    parser.add_argument('--s3', action='store', dest='s3_bucket', default='unrecognized-faces-1')
    parser.add_argument('--dynamo-table', action='store', dest='table', default='local-stats')

    args = parser.parse_args()
    run_on(socket.gethostname(), 8080, args)

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
import future
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import pickle
import json
import operator
from pprint import pprint
import math

# AWS Credentials
AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = getenv('AWS_DEFAULT_REGION', 'eu-west-1')

# Face encodings
AWS_FACE_ENCODINGS_BUCKET = "encodings"
face_encodings_pickle = "encodings.pickle"

# Path variables
unknown = 'unknown'
images_dir = 'images'

class Recognizer():
    _args = None
    # Initialize some variables
    known_images_encoding = []
    _table = None
    _face_encodings = None
    _recognized_faces = []
    _recognized_names = {}

    def __init__(self, args):
        self._args = args
        self._table = boto3.resource(
            'dynamodb', region_name=AWS_REGION).Table(args.table)
        unknown_dir = path.join(images_dir, unknown)
        if not path.exists(unknown_dir):
            makedirs(unknown_dir)

        # Load known pictures
        if not path.isfile(face_encodings_pickle):
            self.download(path.join(AWS_FACE_ENCODINGS_BUCKET,
                                    face_encodings_pickle), face_encodings_pickle)

        self._face_encodings = pickle.loads(
            open("encodings.pickle", "rb").read())
        for name in self._face_encodings["names"]:
            image_dir = path.join(images_dir, name)
            if not path.exists(image_dir):
                makedirs(image_dir)
                print('created %s' % image_dir)

        # Initialize as no face has been recognized
        for i, name in enumerate(self._face_encodings["names"]):
            self._recognized_names[name] = False
            self._recognized_faces.insert(i, False)

        print('finished initialization of Recognizer')


    # Taken from https://github.com/ageitgey/face_recognition/issues/707
    def face_distance_to_conf(self, face_distance, face_match_threshold=0.6):
        if face_distance > face_match_threshold:
            range = (1.0 - face_match_threshold)
            linear_val = (1.0 - face_distance) / (range * 2.0)
            return linear_val
        else:
            range = face_match_threshold
            linear_val = 1.0 - (face_distance / (range * 2.0))
            return linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2))

    # This is not exactly confience but an approximation to it.
    # Open issue remains to use SVN instead of KNN to gather confidence level with matches
    # https://github.com/ageitgey/face_recognition/issues/653

    def printConfidence(self, face_encoding):
        res = list(face_recognition.face_distance(
            self._face_encodings["encodings"],
            face_encoding))

        resMap = {}

        for i, r in enumerate(res):
            resMap[self._face_encodings["files"][i]
                ] = "%f - %f" % (self.face_distance_to_conf(r, 0.5), r)
            # print("%s - %f" % (self._face_encodings["files"][i], 1-r))

        sorted_x = sorted(resMap.items(), key=operator.itemgetter(1), reverse=True)

        maxItems = 5
        for f, confidence in sorted_x:
            print("%s - %s" % (f, confidence))
            maxItems -= 1
            if maxItems == 0:
                break

    def download(self, src, dst):
        # Create an S3 client
        print('downloading %s' % src)
        s3 = boto3.client('s3',
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                          region_name=AWS_REGION)

        s3.download_file(self._args.s3_bucket, src, dst)

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
        encodings = face_recognition.face_encodings(small_frame)

        recognized_faces = dict(self._recognized_names)
        matchedFiles = []

        for face_encoding in encodings:
            # See if the face is a match for the known face(s)
            match = face_recognition.compare_faces(
                self._face_encodings["encodings"],
                face_encoding, 0.5)

            if self._args.verbose:
                self.printConfidence(face_encoding)

            for i, m in enumerate(match):
                name = self._face_encodings["names"][i]
                if m:
                    matchedFiles.append(self._face_encodings["files"][i])
                    recognized_faces[name] = True

        # end of algorithm. no need to track uploading time
        elapsed = str(time.time() - start)
        # # move to recognized or unknown folder
        # image_path = path.join(images_dir, recognized_face, image_name)
        # rename(path.join(images_dir, image_name), image_path)

        # upload only if we cannot recognize the face
        imgdir = path.join(images_dir, image_name)
        if self._args.upload:
            thread = Thread(target=self.upload, args=(
                image_name, imgdir, frame))
            thread.start()

        print ('elapsed time %s' % elapsed)

        db_row = {
            'filename': image_name,
            'created': str(datetime.datetime.utcnow()),
            'duration': elapsed,
            'matchedFiles': json.dumps(matchedFiles)
        }

        for name, result in recognized_faces.iteritems():
            db_row["recognized_" + name] = str(result)

        self._table.put_item(Item=db_row)

        return recognized_faces


class PUTHandler(BaseHTTPRequestHandler):
    recognizer = None
    args = None

    def do_PUT(self):
        if 'Content-Type' not in self.headers or self.headers['Content-Type'] not in ["image/jpeg", "image/jpg"]:
            print ("we only accept image/jpeg types")
            self.send_response(500)
            return
        d = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(204)  # Return early response
        self.end_headers()

        image_name = str(uuid.uuid4()) + ".jpg"
        if 'Filename' in self.headers:
            image_name = self.headers['Filename']
        print("received file %s" % image_name)
        image_path = path.join(images_dir, image_name)

        # load pickle content
        content = pickle.loads(d)

        # save image for later use
        cv2.imwrite(image_path, content)

        names = self.recognizer.recognize(image_name, content, content)
        print("recognized %s" % names)


def run_on(addr, port, args):
    print("Starting a server on port %s:%i" % (addr, port))
    server_address = (addr, port)
    PUTHandler.recognizer = Recognizer(args)
    PUTHandler.args = args
    httpd = HTTPServer(server_address, PUTHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Tracker')
    parser.add_argument('--upload', action='store_true',
                        dest='upload', default=False)
    parser.add_argument('--verbose', action='store_true',
                        dest='verbose', default=False)
    parser.add_argument('--host', action='store',
                        dest='host', default=socket.gethostname())
    parser.add_argument('--s3', action='store',
                        dest='s3_bucket', default='unrecognized-faces-1')
    parser.add_argument('--dynamo-table', action='store',
                        dest='table', default='local-stats')

    args = parser.parse_args()
    run_on(args.host, 8080, args)

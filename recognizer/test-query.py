#!/usr/bin/python

import pickle
import cv2
import argparse
import requests
import os

def send(image, host):
    content = cv2.imread(image)
    if content is None:
        print("[ERROR] failed to read file: %s" % image)
        os._exit(-1)

    try:
        response = requests.put(host,
                                data=pickle.dumps(content),
                                headers={
                                    'content-type': 'image/jpeg'},
                                )
        if response.status_code != 204:
            print("[ERROR] failed to send picture to server: %s" % response.content)
            os._exit(-1)

    except Exception, ex:
        print("[ERROR] failed to communicate with server: %s" % str(ex))
        os._exit(-1)

    print("[INFO] successfuly sent image %s to %s" % (image, host))


parser = argparse.ArgumentParser(description='Face Tracker')
parser.add_argument('--host', action='store',
                    dest='host', default='http://localhost')
parser.add_argument('--image', action='store',
                    dest='image', default='image.jpg')
parser.add_argument('--dir', action='store', dest='dir', default='')

args = parser.parse_args()

if args.dir == "":
    send(args.image, args.host)
    os._exit(0)

for image in os.listdir(args.dir):
    send(os.path.join(args.dir, image), args.host)

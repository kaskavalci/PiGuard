#/usr/bin/python
import cv2
import os
import time, uuid
import requests
import pickle
import argparse
from os.path import join

def upload(args):

    for filename in os.listdir(args.dir):
        print filename
        if filename.endswith(".jpg") or filename.endswith(".jpeg"):
            img = cv2.imread(filename)
            r = requests.put(args.addr, pickle.dumps(
                img), headers={'content-type': 'image/jpeg'})
            if r.status_code == 200:
                print "success!"
            else:
                print r.text

        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Recorder for face recogition database')
    parser.add_argument('--addr', dest='addr', default="http://localhost:8080")
    parser.add_argument('--dir', dest='dir', default=".")

    args = parser.parse_args()

    upload(args)

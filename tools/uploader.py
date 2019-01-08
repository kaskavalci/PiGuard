# /usr/bin/python
import cv2
import os
import time
import uuid
import requests
import pickle
import argparse
from os.path import join
import json

def process(args):

    if os.path.isfile(args.dir):
        filename = args.dir
        start = time.time()
        upload(filename)
        elapsed = time.time() - start
        print("%s - Elapsed: %s" % (filename, str(elapsed)))
        return

    stats = {}

    for filename in os.listdir(args.dir):
        start = time.time()

        upload(filename)

        elapsed = time.time() - start
        stats[filename] = elapsed
        print("%s - Elapsed: %s" % (filename, str(elapsed)))

    with open("stats.json", "w") as f:
        f.write(json.dumps(stats))

def upload(filename):
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        img = cv2.imread(join(args.dir, filename))
        r = requests.put(args.addr,
                            pickle.dumps(img),
                            headers={
                                'content-type': 'image/jpeg',
                                'Filename': filename})
        if r.status_code == 204:
            print "success!"
        else:
            print r.text

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Face Recorder for face recogition database')
    parser.add_argument('--addr', dest='addr', default="http://localhost:8080")
    parser.add_argument('--dir', dest='dir', default=".")

    args = parser.parse_args()

    process(args)

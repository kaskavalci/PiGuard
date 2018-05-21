#/usr/bin/python
import cv2
import time, uuid
import requests
import pickle
import argparse
from os.path import join

def crop(frame, bbox):
    return frame[int(bbox[1]): int(bbox[1]) + int(bbox[3]), int(bbox[0]): int(bbox[0]) + int(bbox[2])]

def record(args):
    video_capture = cv2.VideoCapture(0)
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    idx = args.idx

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(faces) == 0:
            print "skipping -- cannot detect a face"
            time.sleep(1)
            continue
        if len(faces) > 1:
            print "skipping -- multiple faces found"
            time.sleep(1)
            continue
        face = crop(gray, faces[0])

        if args.upload:
            headers = {'content-type': 'image/jpeg'}
            r = requests.put(args.addr, pickle.dumps(face), headers=headers)
            if r.status_code == 200:
                print "success!"
            else:
                print r.text
        if args.save:
            idx = idx + 1
            filename = "%s_%03d.jpg" % (args.name, idx,)
            # filename = args.name + "_" + str(idx) + ".jpg"
            dst = join(args.name, filename)
            cv2.imwrite(dst, face)
            print "written " + filename
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Recorder for face recogition database')
    parser.add_argument('--upload', action='store_true', dest='upload', default=False)
    parser.add_argument('--addr', dest='addr', default="http://localhost:8080")
    parser.add_argument('--save', action='store_true', dest='save', default=True)
    parser.add_argument('--name', dest='name', required=True)
    parser.add_argument('--idx', dest='idx', default=0)

    args = parser.parse_args()

    record(args)

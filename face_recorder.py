#!/usr/bin/env python

# note to self
# implement threading. grab with a thread and get the latest frame from the cam

import base64
import time
import urllib2

import cv2
import operator
# import sys
import argparse
# import numpy as np
# import boto3
import datetime
import threading

"""
Examples of objects for image frame aquisition from both IP and
physically connected cameras

Requires:
 - opencv (cv2 bindings)
 - numpy
"""


class FaceTracker:
    Face = None
    Tracker = None
    __faceCascade = None
    __eyesCascade = None
    __expand = (-50, -50, 50, 50)
    __resolution = None
    __args = None
    __vcap = None
    __grabberThread = None

    def __init__(self, args, tracker=None, faceCascade=None, eyesCascade=None):
        self.__args = args

        if tracker is None:
            self.Tracker = cv2.Tracker_create("KCF")
        if faceCascade is None:
            self.__faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
        if eyesCascade is None:
            self.__eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

        self.initcam()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # When everything is done, release the capture
        self.__grabberThread.do_grab = False
        self.__grabberThread.join()

        if self.__args.showimage or self.__args.showface:
            cv2.destroyAllWindows()
        self.__vcap.release()

    def grabber(self):
        while getattr(self.__grabberThread, "do_grab", True):
            self.__vcap.grab()

        print 'Exiting grab thread'

    def initcam(self):
        if self.__args.ipcam:
            url = "rtsp://192.168.1.10:554/user=admin&password=&channel=1&stream=1.sdp?real_stream--rtp-caching=100"
            # url = "rtsp://192.168.1.10:554/user=admin&password=&channel=1&stream=1"
            self.__vcap = cv2.VideoCapture(url)
        else:
            self.__vcap = cv2.VideoCapture(0)

        self.__vcap.set(cv2.CAP_PROP_FPS, 1)
        self.__vcap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

        w = self.__vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.__vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.__resolution = (w, h)

    def run(self):
        err_counter = 0
        self.__grabberThread = threading.Thread(target=self.grabber)
        self.__grabberThread.start()

        fail_count = 0
        while True:
            retval, frame = self.__vcap.retrieve()
            if not retval:
                fail_count += 1
                continue

            if fail_count > 1:
                print 'failed to get image {} times'.format(fail_count)
                fail_count = 0

            if self.__args.showimage:
                cv2.imshow('img', frame)

            if self.__args.saveimage:
                date = datetime.datetime.now()
                cv2.imwrite('i_{}.jpg'.format(date.isoformat()), frame)

            faces = self.find_faces(frame)
            if faces is not None:
                print '{} faces found'.format(len(faces))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def find_faces(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.__faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            # minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) == 0:
            return

        for face in faces:
            expanded = self.expand_face(face)
            print expanded
            (x, y, w, h) = expanded
            crop = img[y: y + h + 100, x: x + w + 100]
            if self.__args.saveface:
                date = datetime.datetime.now()
                cv2.imwrite('{}.jpg'.format(date.isoformat()), crop)
            if self.__args.showface:
                cv2.imshow('face', crop)
            # img = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

        return faces

    def expand_face(self, bbox):
        updated = list(map(operator.add, bbox, self.__expand))
        # Perform region check
        for i in range(0, 4):
            updated[i] = max(0, updated[i])
            updated[i] = min(self.__resolution[i % 2], updated[i])

        return tuple(updated)

    def init_tracker(self, frame):
        faces = self.find_faces(frame)
        if len(faces) == 0:
            return False
        self.Face = faces[0]
        # Recognize face now
        # TODO: upload to aws

        return True

    def crop(self, frame, bbox):
        return frame[int(bbox[1]): int(bbox[1]) + int(bbox[3]), int(bbox[0]): int(bbox[0]) + int(bbox[2])]

    def rectangle_face(self, frame):
        if self.Face is None:
            return
        p1 = (int(self.Face[0]), int(self.Face[1]))
        p2 = (int(self.Face[0] + self.Face[2]), int(self.Face[1] + self.Face[3]))
        cv2.rectangle(frame, p1, p2, (0,0,255))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Tracker')
    # parser.add_argument('--webcam', action='store_false', dest='webcam', default=True)
    parser.add_argument('--ipcam', action='store_true', dest='ipcam', default=False)
    parser.add_argument('--save-face', action='store_true', dest='saveface', default=False)
    parser.add_argument('--save-image', action='store_true', dest='saveimage', default=False)
    parser.add_argument('--show-face', action='store_true', dest='showface', default=False)
    parser.add_argument('--show-image', action='store_true', dest='showimage', default=False)

    args = parser.parse_args()

    with FaceTracker(args=args) as faceTracker:
        faceTracker.run()

    # try:
    #     faceTracker.run()
    # except Exception as e:
    #     print 'Failed {}'.format(e.message)

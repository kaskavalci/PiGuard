#!/usr/bin/env python

# note to self
# implement threading. grab with a thread and get the latest frame from the cam

import base64
import time
import urllib2

import cv2
import operator
import sys
import os
import argparse
# import numpy as np
# import boto3
import datetime
import threading
import logging
import requests
import pickle

"""
Examples of objects for image frame aquisition from both IP and
physically connected cameras

Requires:
 - opencv (cv2 bindings)
 - numpy
"""


class FaceTracker:
    Face = None
    __faceCascade = None
    __eyesCascade = None
    __expand = (-50, -50, 50, 50)
    __resolution = None
    __args = None
    __vcap = None
    __grabberThread = None
    __camLock = threading.Lock()
    __previousFrame = None

    def __init__(self, args, faceCascade=None, eyesCascade=None):
        self.__args = args

        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

        if faceCascade is None:
            self.__faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
        if eyesCascade is None:
            self.__eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # When everything is done, release the capture
        logging.info('received exit signal, quiting everything')
        if getattr(self.__grabberThread, "do_grab", True):
            self.__grabberThread.do_grab = False
            self.__grabberThread.join()
        logging.info('stopping cv2 instances')
        if self.__args.showimage or self.__args.showface:
            cv2.destroyAllWindows()
        self.__vcap.release()
        logging.info('RIP')

    def grabber(self):
        i = 0
        logging.debug('grabber thread started')
        while getattr(self.__grabberThread, "do_grab", True):
            self.__camLock.acquire()
            self.__vcap.grab()
            self.__camLock.release()
            i += 1

        logging.info('grab thread finished')

    def startGrabber(self):
        logging.debug('starting grabber thread')
        self.__grabberThread.start()

    def stopGrabber(self):
        logging.debug('stopping grabber thread')
        self.__grabberThread.do_grab = False
        self.__grabberThread.join()
        logging.info('stopped grabber thread')

    def isThereMotion(self, frame):
        blur = cv2.GaussianBlur(frame, (21, 21), 0)
        if self.__previousFrame is None:
            self.__previousFrame = blur
            return True

        # compute the absolute difference between the current frame and
        # first frame
        frameDelta = cv2.absdiff(self.__previousFrame, blur)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        _, contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.__previousFrame = blur

        if len(contours) > 0:
            logging.debug('motion detected')
            return True

        logging.debug('no motion found')
        return False

    def initcam(self):
        logging.info('initing camera')
        if self.__args.ipcam:
            if self.__args.cache:
                url = "rtsp://192.168.1.10:554/" \
                "user=admin&password=&channel=1&stream=1.sdp?real_stream--rtp-caching=100"
            else:
                url = "rtsp://192.168.1.10:554/user=admin&password=&channel=1&stream=1.sdp"
            self.__vcap = cv2.VideoCapture(url)
            logging.info('IPcam set to {}'.format(url))
        elif self.__args.video != '':
            self.__vcap = cv2.VideoCapture(self.__args.video)
        else:
            self.__vcap = cv2.VideoCapture(0)
            logging.info('using webcam')

        self.__vcap.set(cv2.CAP_PROP_FPS, 1)
        self.__vcap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

        w = self.__vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.__vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.__resolution = (w, h)

        self.__grabberThread = threading.Thread(target=self.grabber)
        self.startGrabber()
        logging.info('inited cam')

    def run(self):
        err_counter = 0
        fail_count = 0
        motionless_count = 0

        self.initcam()

        while True:
            if fail_count > 500 or motionless_count > 500:
                logging.info('too many failures or no motion. reiniting cam')
                self.stopGrabber()
                self.initcam()
                fail_count = 0
                motionless_count= 0
            self.__camLock.acquire()
            retval, frame = self.__vcap.retrieve()
            self.__camLock.release()
            if not retval:
                fail_count += 1
                continue

            if fail_count > 1:
                logging.info('failed to get image {} times'.format(fail_count))
                fail_count = 0

            img = cv2.resize(frame, (1024, 768))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if self.__args.showimage:
                cv2.imshow('img', frame)

            if not self.isThereMotion(gray):
                motionless_count += 1
                continue

            faces = self.find_faces(gray)
            if faces is not None:
                logging.info('{} faces found'.format(len(faces)))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def find_faces(self, img):

        date = datetime.datetime.now()

        if self.__args.saveimage:
            fname = 'i_{}.jpg'.format(date.isoformat())
            cv2.imwrite(os.path.join('images', fname), img)

# First window: (20*20 | 300*300) is capable of 4 meters distance,
# Second window (50*50 | 250*250) can detect 3.7 meters
# Third window (80*80 | 200*200) detects 3 meters away.
        faces = self.__faceCascade.detectMultiScale(
            img,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20),
            maxSize=(300, 300),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(faces) == 0:
            return

        for face in faces:
            crop = self.crop(img, face)
            if self.__args.expand:
                expanded = self.expand_face(face)
                logging.info("exanped: " + str(expanded))
                (x, y, w, h) = expanded
                crop = img[y: y + h + 100, x: x + w + 100]
            fname = date.isoformat() + '.jpg'
            fpath = os.path.join('images', fname)
            if self.__args.saveface:
                cv2.imwrite(fpath, crop)
            if self.__args.showface:
                cv2.imshow('face', crop)
            if self.__args.upload:
                self.upload(img, fname)

        return faces

    def upload(self, picture, fname):
        try:
            _, img_encoded = cv2.imencode('.jpg', picture)
            response = requests.put(self.__args.host,
                                    data=pickle.dumps(img_encoded),
                                    headers={
                                        'content-type': 'image/jpeg', 'Filename': fname},
                                    )
            if response.status_code != 204:
                logging.error(
                    'failed to send picture to server: {}'.format(response.content))
        except:
            print("web server is not available")

    def expand_face(self, bbox):
        updated = list(map(operator.add, bbox, self.__expand))
        # Perform region check
        for i in range(0, 4):
            updated[i] = max(0, updated[i])
            updated[i] = min(self.__resolution[i % 2], updated[i])

        return tuple(updated)

    def crop(self, frame, bbox):
        return frame[int(bbox[1]): int(bbox[1]) + int(bbox[3]), int(bbox[0]): int(bbox[0]) + int(bbox[2])]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Tracker')
    parser.add_argument('--ipcam', action='store_true', dest='ipcam', default=False)
    parser.add_argument('--video', action='store', dest='video', default='', help='Use a video input instead of a camera')
    parser.add_argument('--cache', action='store_true', dest='cache', default=False)
    parser.add_argument('--save-face', action='store_true', dest='saveface', default=False)
    parser.add_argument('--save-image', action='store_true', dest='saveimage', default=False)
    parser.add_argument('--upload', action='store_true', dest='upload', default=False)
    parser.add_argument('--host', action='store', dest='host', default='http://192.168.1.129:8082/')
    parser.add_argument('--show-face', action='store_true', dest='showface', default=False)
    parser.add_argument('--show-image', action='store_true', dest='showimage', default=False)
    parser.add_argument('--min-area', type=int, dest='minarea', default=600)
    parser.add_argument('--expand-face', action='store_true', dest='expand', default=False)

    args = parser.parse_args()

    with FaceTracker(args=args) as faceTracker:
        try:
            faceTracker.run()
        except KeyboardInterrupt:
            print 'Interrupted'
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

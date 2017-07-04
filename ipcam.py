#!/usr/local/bin/python

import base64
import time
import urllib2

import cv2
import operator
import sys
import argparse
import numpy as np

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
    __expand = (-50.0, -50.0, 50.0, 50.0)
    __resolution = None

    def __init__(self, tracker=None, faceCascade=None, resolution=None):
        if tracker is None:
            self.Tracker = cv2.Tracker_create("KCF")
        if faceCascade is None:
            self.__faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')

        self.__resolution = resolution

    def find_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.__faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        return faces

    def expand_poi(self, bbox):
        updated = list(map(operator.add, bbox, self.__expand))
        # Perform region check
        for i in range(0, 4):
            updated[i] = max(0, updated[i])
            updated[i] = min(self.__resolution[i % 2], updated[i])

        return tuple(updated)

    def reinit_tracker(self):
        if self.Face is None:
            return False
        poi = self.Face
        face_center = (abs(int(poi[2] - poi[0])), abs(int(poi[3] - poi[1])))
        updated = self.expand_poi(poi)

        success = False

        for i in range(0, 10):
            cropped = self.crop(frame, updated)
            faces = self.find_faces(cropped)
            if len(faces) == 0:
                updated = self.expand_poi(updated)
                continue

            dist = []
            for face in faces:
                center = (abs(int(face[2] - face[0])), abs(int(face[3] - face[1])))
                dist.append(cv2.norm(face_center, center))

            min_index, min_value = min(enumerate(dist), key=operator.itemgetter(1))
            print 'found face after reinit'
            self.Face = faces[min_index]
            self.Tracker.init(frame, (self.Face[0], self.Face[1], self.Face[2], self.Face[3]))
            return


        return False

    def init_tracker(self, frame):
        faces = self.find_faces(frame)
        if len(faces) == 0:
            return False
        self.Face = faces[0]
        # Recognize face now
        # TODO: upload to aws
        ok = self.Tracker.init(frame, (self.Face[0], self.Face[1], self.Face[2], self.Face[3]))
        if not ok:
            print 'failed to init tracker!'
        print 'inited tracker'
        return True

    def update(self, frame):
        ok, bbox = self.Tracker.update(frame)
        if not ok:
            print 'Cannot update tracker'
            # Setting Face to None re-initializes the tracker and face
            self.Face = None
            return False
        # find face in the new poi
        cropped = self.crop(frame, bbox)
        cv2.imshow('cropped', cropped)
        faces = self.find_faces(cropped)
        if len(faces) == 0:
            print 'Lost the face. Expanding'
            if self.reinit_tracker():
                print 'Failed to find face'
                self.Face = None
        else:
            print 'face is stable'
            self.Face = faces[0]
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
    args = parser.parse_args()

    if args.ipcam:
        # vcap = cv2.VideoCapture("rtsp://192.168.1.10:554/user=admin&password=&channel=1&stream=1")
        vcap = cv2.VideoCapture("rtsp://192.168.1.10:554/user=admin&password=&channel=1&stream=1.sdp?real_stream--rtp-caching=100")
    else:
        vcap = cv2.VideoCapture(0)

    errCounter = 0
    vcap.set(cv2.CAP_PROP_FPS, 1)
    w = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    faceTracker = FaceTracker(resolution=(w, h))

    while True:
        for i in range(5):
            # Redundant read to clear buffer
            ret, frame = vcap.read()
        if not ret:
            print "Error while reading input"
            errCounter += 1
            if errCounter > 10:
                break
            continue
        # frame = cv2.resize(frame, (800, 680))
        if faceTracker.Face is None:
            inited = faceTracker.init_tracker(frame)

        if inited and faceTracker.update(frame):
            faceTracker.rectangle_face(frame)

        cv2.imshow('face', frame)

            # for (x, y, w, h) in faces:
            #     bbox = (x, y, w, h)
            #     ok = tracker.init(frame, bbox)
            #
            #     ok, bbox = tracker.update(frame)
            #     if ok:
            #         p1 = (int(bbox[0]), int(bbox[1]))
            #         p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            #         cv2.rectangle(frame, p1, p2, (0,0,255))
            #
            #     # crop = frame[y: y + h, x: x + w]
            #     # cv2.imwrite("face.jpg", crop)
            #     cv2.imshow('face', crop)

        # cv2.imshow('VIDEO', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything is done, release the capture
    vcap.release()
    cv2.destroyAllWindows()

#/usr/bin/python
import cv2
import time
import uuid
import requests
import pickle
import argparse
from os.path import isfile, join, splitext
from os import listdir
import os

def crop(frame, bbox):
    return frame[int(bbox[1]): int(bbox[1]) + int(bbox[3]), int(bbox[0]): int(bbox[0]) + int(bbox[2])]

def load(args):
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    counter = 0
    for file in os.listdir(args.input):
        if file.endswith(".jpg"):
            image_path = os.path.join(args.input, file)
            frame = cv2.imread(image_path)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            i = 0
            for f in faces:
                face = crop(gray, f)
                counter = counter + 1
                filename, file_extension = splitext(file)
                output_filename = filename + str(i) + file_extension
                image_output_path = os.path.join(args.output, output_filename)
                cv2.imwrite(image_output_path, face)
                print('written %s' % image_output_path)
                i = i + 1

    print('cropped %d faces' % counter)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Face Recorder for face recogition database')
    parser.add_argument('--output', action='store', dest='output', required=True)
    parser.add_argument('--input', action='store', dest='input', required=True)

    args = parser.parse_args()

    load(args)


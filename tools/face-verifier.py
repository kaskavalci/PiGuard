# Face verifier reads a directory containing images tries to detect an image
# haarcascade_frontalface_default.xml is used
import numpy as np
from imutils import paths
import argparse
import cv2

faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
# First window: (20*20 | 300*300) is capable of 4 meters distance,
# Second window (50*50 | 250*250) can detect 3.7 meters
# Third window (80*80 | 200*200) detects 3 meters away.
# Hard-coded settings are from
# WAZWAZ, Ayman A., et al. Raspberry Pi and computers-based face detection and recognition system.
# In: 2018 4th International Conference on Computer and Technology Applications (ICCTA). IEEE, 2018. p. 171-174.
settings = [
    {
        "minSize": (20, 20),
        "maxSize": (300, 300),
        "sf": 1.1,
        "mn": 5,
    },
    {
        "minSize": (50, 50),
        "maxSize": (250, 250),
        "sf": 1.1,
        "mn": 6,
    },
    {
        "minSize": (80, 80),
        "maxSize": (200, 200),
        "sf": 1.2,
        "mn": 6,
    },
    ]

def read_directory(args):
    imagePaths = list(paths.list_images(args["dataset"]))

    setting = settings[args["window"] - 1]

    faceless = 0
    total = 0

    for (i, imagePath) in enumerate(imagePaths):
        image = cv2.imread(imagePath)
        faces = faceCascade.detectMultiScale(
            image,
            scaleFactor=setting["sf"],
            minNeighbors=setting["mn"],
            minSize=setting["minSize"],
            maxSize=setting["maxSize"],
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        # print("no %d faces found in %s" % (len(faces), imagePath))
        total += 1
        if len(faces) == 0:
            # print("no face found in " + imagePath)
            faceless +=1

    error = float(faceless) / float(total)
    print("Number of faceless frames %d / %d" % (faceless, total))
    print("Error rate %f" % (error))

if __name__ == "__main__":
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--dataset", required=True,
                    help="path to input directory of faces + images")
    ap.add_argument("-w", "--window", type=int, default=2,  choices=[1, 2, 3],
                    help="window for the face. How far the face will be from the camera. 1: 4m 2: 3,7m 3: 3m")
    args = vars(ap.parse_args())

    read_directory(args)

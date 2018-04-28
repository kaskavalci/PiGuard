FROM rickryan/rpi-jessie-opencv3.2

RUN pip install requests face_recognition boto3

ADD . /recognizer
WORKDIR /recognizer

CMD ["recog.py"]

FROM rickryan/rpi-jessie-opencv3.2

RUN pip install requests face_recognition boto3

ADD . /recognizer
WORKDIR /recognizer

ENTRYPOINT [ "python", "./recog.py" ]
CMD ["--upload"]

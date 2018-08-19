FROM rickryan/rpi-jessie-opencv3.2

RUN pip install requests face_recognition boto3 future

ADD . /recognizer
WORKDIR /recognizer

ENTRYPOINT [ "python", "-u", "./recog.py" ]
CMD ["--upload"]

FROM kaskavalci/face_recognition

RUN pip install requests boto3 future

ADD . /recognizer
WORKDIR /recognizer

ENTRYPOINT [ "python", "-u", "./recog.py" ]
CMD ["--upload"]

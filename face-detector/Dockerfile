FROM rickryan/rpi-jessie-opencv3.2

ADD . /face-detector/
WORKDIR /face-detector

CMD ["./face-detector.py", "--upload", "--ipcam"]

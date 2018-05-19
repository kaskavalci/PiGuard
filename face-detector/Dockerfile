FROM rickryan/rpi-jessie-opencv3.2

ADD . /face-detector/
WORKDIR /face-detector

ENTRYPOINT [ "python", "-u", "./face-detector.py" ]
CMD ["--upload", "--ipcam"]

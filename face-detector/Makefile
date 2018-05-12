.PHONY: run build
.DEFAULT_GOAL := run

run:
	docker run \
	    -d \
	    --restart=unless-stopped \
		-v `pwd`/images:/face-detector/images \
		face-detector

build:
	docker build -t face-detector .

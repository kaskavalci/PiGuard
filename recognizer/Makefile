.PHONY: build run
.DEFAULT_GOAL := build

build:
	docker build -t recognizer .

run:
	docker run -e "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" \
		-e "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" \
		-d \
		--restart=unless-stopped \
		-p 8080:8080 \
		-v known_images:/recognizer/known_images \
		-v unrecognized:/recognizer/unrecognized \
		recognizer

get:
	mkdir -p ./known_images
	mkdir -p ./unrecognized
	aws s3 cp s3://known-faces ./known_images/ --recursive

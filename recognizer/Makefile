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
		-v `pwd`/known_images:/recognizer/known_images \
		-v `pwd`/images:/recognizer/images \
		recognizer

get:
	mkdir -p ./known_images
	aws s3 cp s3://known-faces ./known_images/ --recursive

install-dep:
	pip install --upgrade --user -r requirements.txt

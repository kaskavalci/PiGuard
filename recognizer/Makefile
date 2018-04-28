.PHONY: build run
.DEFAULT_GOAL := build

build:
	docker build -t recognizer .

run:
	docker run -e "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" \
		-e "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" \
		-d \
		--restart=unless-stopped \
		recognizer


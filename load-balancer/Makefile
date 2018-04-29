.PHONY: run build
.DEFAULT_GOAL := run

run:
	docker run \
	    -d \
	    --restart=unless-stopped \
		-p 8082:8082 \
		lb

build:
	docker build -t lb .

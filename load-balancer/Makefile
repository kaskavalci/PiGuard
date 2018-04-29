.PHONY: run
.DEFAULT_GOAL := run

run:
	docker run \
	    -d \
	    --restart=unless-stopped \
	    --rm \
		-p 8082:8082 \
		lb

# BUILD
FROM golang:1.11.4-alpine3.8

RUN apk add --no-cache git make musl-dev gcc
RUN go get -u github.com/JackyChiu/slb
WORKDIR /go/src/github.com/JackyChiu/slb
RUN make all

# RUNTIME
FROM alpine:3.8
COPY --from=0 /go/src/github.com/JackyChiu/slb/bin/slb /app/

WORKDIR /app/

ENTRYPOINT ["./slb"]
CMD ["-strategy", "round_robin", "-config", "config/config.json"]

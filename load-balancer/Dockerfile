# BUILD
FROM golang:1.10.1-alpine3.7

RUN apk add --no-cache git make
RUN go get -u github.com/JackyChiu/slb
WORKDIR /go/src/github.com/JackyChiu/slb
RUN make all

# RUNTIME
FROM alpine:3.7
COPY --from=0 /go/src/github.com/JackyChiu/slb/bin/slb /app/

WORKDIR /app/
ADD config.json /app/

CMD ["slb", "-strategy", "round_robin", "-config", "config.json"]

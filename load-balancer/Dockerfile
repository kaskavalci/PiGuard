FROM golang:1.10.1-alpine3.7

RUN apk add --no-cache git make
RUN go get -u github.com/JackyChiu/slb
WORKDIR /go/src/github.com/JackyChiu/slb
RUN make all
ADD config.json /go/src/github.com/JackyChiu/slb/

CMD ["./bin/slb", "-strategy", "round_robin", "-config", "config.json"]

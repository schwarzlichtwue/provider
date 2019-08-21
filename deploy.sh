#!/bin/sh

docker build -t schwarzlicht-wue-content-provider ./
docker stack deploy --compose-file docker-stack.yml sl

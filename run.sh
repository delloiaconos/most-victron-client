#!/bin/bash 
mkdir -p logs

docker run --rm -d --name mvc-testing \
    -v "$PWD/logs:/app/logs" \
    most-victron-client:testing

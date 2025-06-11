#!/bin/bash 
docker build --platform linux/amd64 -t most-victron-client:testing -f Dockerfile .

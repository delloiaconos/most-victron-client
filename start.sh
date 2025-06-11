#!/bin/bash

# This script is used to start the application in a Docker container.
python /app/main.py #> /app/logs/output.log 2>&1 
# most-victron-client

**A lightweight docker container for maintaining a reliable connection to the Victron MQTT broker.**

# Overview

This project implements a container and a threaded Python system that connects to a Victron MQTT broker, performing regular keepalive checks, and gracefully handling disconnections by restarting the connection logic.
It is optimized for use in Docker containers and uses only the minimal required dependencies.


## Architecture

The application is split across three main threads implemented in two classes:

- **`thdKeepAlive`**:  
  A thread responsible for sending periodic keepalive pings to check the health of the connection.

- **`thdReceiver`**:  
  A thread that handles the MQTT connection and data reception from the Victron broker.

- **Main Controller** (in `main.py` or equivalent):  
  Manages the lifecycle of the threads:
  - Starts and monitors the keepalive and receiver threads.
  - Automatically stops and restarts the receiver if the keepalive thread indicates a failure (with some hysteresis to avoid flapping).
  - Planned: Periodically checks the MQTT broker address for changes.


## Features

- **Thread-based concurrency**: Simple and robust compared to multiprocessing in Docker.
- **Graceful recovery**: Auto-restarts receiver thread on connection failure.
- **Minimal dependencies**: Only core libraries and essentials:
  - `paho-mqtt`
  - `requests`
  - `json`
  - `ssl`
  - `configparser`
  - `influxdb` 
- **Configurable via INI**: Easily adjustable settings through a config file.
- **Structured logging**: Outputs logs in format `[CLASS] (YYYY-MM-DD HH:MM:SS)`.


## Status
[x] Stable core implementation
[x] Integrated logging
[x] Docker-friendly

[] Dynamic broker IP re-check (planned)
[] Topic parsing from Victron's VE.PROTOCOL 3.34 


## Current Testing & Deployment

This client is currently being tested with a Victron Cerbo GX test unit in the lab.
- Confirmed operational for over 12 hours continuously.
- Successfully runs in a Docker container (most-giroe-victron:sdi).
- Coexists with older container instances without issue.
- Manual disconnection testing is ongoing to confirm resilience.



# Usage

## Local Testing

Clone the repo and set up your testing environment:

```bash
git clone https://github.com/delloiaconos/MOST-Victron-Clinet.git
cd most-victron-client
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python main.py
```


## Docker testing


This project includes two helper scripts: `build.sh` and `run.sh` to simplify Docker image creation and container management.

### 1. Build the Docker Image

The `makefile` script can build and run the Docker image for the Victron MQTT client.

```bash
make build
```

This command:
- Executes docker build using the local Dockerfile.
- Tags the image (e.g., `most-victron-client:devel` — check your script for the exact tag).


### 2. Run the Docker Container
To start a new container from the previously built image, use the following command:

```bash
make run
```
This command:
- Launches the Docker container using the last devel image available.
- Mounts required volumes or binds configuration files (e.g., development.ini).


### Use ansible to deploy

1. Install ansible
```bash

```

2. Install collections:
```bash
ansible-galaxy collection install community.docker
```

3. Run the playbook 
```bash
ansible-playbook create_containers.yml --ask-become-pass
```

# Git & Collaboration
This project is version-controlled via Git for clarity and development hygiene — no CI/CD or advanced Git-based deployments are planned.
If you'd like access to the repository, just ask the maintainer.

# References
Victron VE.Direct Protocol v3.34


# Fundings
This study was carried out within the MOST - Sustainable Mobility National Research Center and received funding from the European Union Next-GenerationEU (PIANO NAZIONALE DI RIPRESA E RESILIENZA (PNRR) - MISSIONE 4 COMPONENTE 2, INVESTIMENTO 1.4 - D.D. 1033 17/06/2022, CN00000023), Spoke 5 "Light Vehicle and Active Mobility". 
This work/code/repository reflects only the authors’ views and opinions, neither the European Union nor the European Commission can be considered responsible for them.


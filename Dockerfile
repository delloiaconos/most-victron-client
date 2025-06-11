# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-alpine

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
# ENV VIRTUAL_ENV=/opt/venv
# RUN python3 -m venv $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"


#alpine
RUN apk add --no-cache openssh-client mosquitto-clients
#almalinux 

# Authorize SSH Host
#RUN mkdir -p /root/.ssh && \
#    chmod 0700 /root/.ssh

#COPY elmos-deploy.id_rsa /root/.ssh/id_rsa
#RUN chmod 600 /root/.ssh/id_rsa && ssh-keyscan bitbucket.org > /root/.ssh/known_hosts
# RUN export GIT_SSH_COMMAND="ssh -i /root/.ssh/deploy.id_rsa "

RUN pip install --upgrade pip

# Remove SSH keys
#RUN rm -rf /root/.ssh/

WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt


RUN mkdir /app/config
RUN mkdir /app/logs

COPY venus-ca.crt /app/
COPY intermediate_ca.pem /app/intermediate_ca.pem

COPY config/config.ini /app/config/
COPY start.sh /app/
COPY main.py /app/
COPY thdKeepAlive.py /app/
COPY thdReceiver.py /app/
COPY thdSender.py /app/

#COPY config/receiver-config.yaml /app/config/
#COPY config/vrm.yaml /app/config/

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# delete unusued packages


# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["/bin/sh", "/app/start.sh"]
# CMD /bin/sh

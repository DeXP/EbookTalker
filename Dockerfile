# syntax=docker/dockerfile:1
FROM python:3.13-slim

# set work directory
WORKDIR /usr/src/app/

# install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# install runtime depenencies
ENV RUNTIME_DEPENDENCIES="ffmpeg"

RUN apt-get update \
    && apt-get install -y $RUNTIME_DEPENDENCIES \
&& rm -rf /var/lib/apt/lists/*

# copy project
COPY . .
COPY default-docker.cfg default.cfg

# run app
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0" ]

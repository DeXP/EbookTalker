# syntax=docker/dockerfile:1
FROM python:3.13-slim

ARG TORCH_URL=""
ENV TORCH_URL=$TORCH_URL

# set work directory
WORKDIR /usr/src/app/

# install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install torch --no-cache-dir ${TORCH_URL}

# install runtime depenencies
RUN apt-get update \
    && apt-get install -y ffmpeg --no-install-recommends \
&& rm -rf /var/lib/apt/lists/*

# copy project
COPY . .
COPY default-docker.cfg default.cfg

# run app
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0" ]

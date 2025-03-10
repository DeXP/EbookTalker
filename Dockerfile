# syntax=docker/dockerfile:1
FROM python:3.13-slim

# set work directory
WORKDIR /usr/src/app/

# install dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# run app
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0" ]

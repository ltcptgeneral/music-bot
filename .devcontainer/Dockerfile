FROM python:slim
WORKDIR /
RUN apt-get -y update; apt-get -y upgrade
RUN apt-get -y install git binutils xxd
RUN apt-get -y install python3 python3-dev git python3-pip python-is-python3 libgl1-mesa-dev build-essential ffmpeg
COPY requirements.txt .
RUN pip install -r requirements.txt
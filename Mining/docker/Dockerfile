FROM python:3.10
MAINTAINER THE MLEXCHANGE TEAM

RUN ls
COPY docker/requirements.txt requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    python3-pip\
    ffmpeg\
    libsm6\
    libxext6 

RUN pip3 install --upgrade pip &&\
    pip3 install -r requirements.txt 

WORKDIR /app/mining
ENV HOME /app/mining
COPY src src
ENV PYTHONUNBUFFERED=1

CMD bash
WORKDIR /app/mining/src
CMD python3 update_db.py
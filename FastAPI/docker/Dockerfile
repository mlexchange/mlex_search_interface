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

#EXPOSE 8060

WORKDIR /app/fastapi
ENV HOME /app/fastapi
COPY src src
ENV PYTHONUNBUFFERED=1

CMD bash
WORKDIR /app/fastapi/src
#CMD uvicorn main:app --reload
CMD uvicorn main:app --host 0.0.0.0 --port 8060 --reload
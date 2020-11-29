FROM python:3.8

COPY . /app

WORKDIR /app

RUN apt install -y git

RUN pip install -r requirements.txt

EXPOSE 80
FROM python:3.9.18-bullseye

ENV PYTHONFAULTHANDLER=1 \
     PYTHONUNBUFFERED=1 \
     PYTHONDONTWRITEBYTECODE=1 \
     PIP_DISABLE_PIP_VERSION_CHECK=on

RUN apt update 
RUN apt install -y ffmpeg jq


CMD ["bash", "-c",  "/app/start"]

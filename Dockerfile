FROM python:3.9
WORKDIR /
RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-venv && \
    apt-get install -y ffmpeg && apt-get install libopus0
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY . /
CMD python bot.py
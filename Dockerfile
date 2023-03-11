FROM python:3.9
WORKDIR /bot
RUN apt-get update && apt-get install --no-install-recommends -y python3.9 python3-venv && \
    apt-get install -y ffmpeg && apt-get install libopus0
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python bot.py
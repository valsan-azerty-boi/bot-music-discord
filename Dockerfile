FROM python:3.9
WORKDIR /bot
RUN apt-get update && apt-get install --no-install-recommends -y python3 python3-venv && \
    apt-get install -y ffmpeg && apt-get install libopus0 && apt-get install nano
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN pip install -U https://github.com/coletdjnz/yt-dlp-youtube-oauth2/archive/refs/heads/master.zip
COPY . /bot
CMD python bot.py
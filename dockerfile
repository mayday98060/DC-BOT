FROM jrottenberg/ffmpeg:4.4-ubuntu1804

# 同樣地，安裝 Python(如果該基底映像檔沒有預裝 Python)
RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "bot.py"]

FROM python:3.10-slim

# 필요한 패키지 설치 (버전에 맞는 chromium-driver 포함)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    xdg-utils \
    fonts-liberation \
    wget \
    unzip

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PATH=$PATH:/usr/bin/chromium:/usr/bin/chromedriver

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

# 앱 복사
COPY . /app
WORKDIR /app

# 포트 열기
EXPOSE 8501

# Streamlit 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]

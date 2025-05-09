FROM python:3.10-slim

# 기본 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libgbm1 \
    libu2f-udev \
    xdg-utils \
    chromium \
    chromium-driver

# 환경 변수 설정
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="$PATH:/usr/bin/chromium"

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 복사
COPY . /app
WORKDIR /app

# Streamlit 포트
EXPOSE 8501

# 실행 명령
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]

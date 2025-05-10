FROM python:3.10

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    xdg-utils \
    chromium \
    chromium-driver

# 환경 변수로 크롬 경로 지정
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . .

# Streamlit 실행
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]

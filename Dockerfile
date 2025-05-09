FROM python:3.10-slim

# Install Chromium 124 and Chromedriver 124
RUN apt-get update && apt-get install -y \
    chromium-browser \
    fonts-liberation \
    libnss3 \
    unzip \
    curl

# ChromeDriver for version 124
RUN curl -Lo /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/linux64/chromedriver-linux64.zip && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf /tmp/*



# 환경변수
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PATH=$PATH:/usr/bin/chromium:/usr/bin/chromedriver

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 복사
COPY . /app
WORKDIR /app

EXPOSE 8501

# 앱 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]

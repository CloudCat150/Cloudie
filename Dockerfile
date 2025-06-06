# Python 3.11 기반 슬림한 이미지
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libopus0 \
    libopus-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

# libopus.so가 제대로 로드되도록 경로를 환경변수에 포함
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib

# 실행 (환경변수 DISCORD_TOKEN은 외부에서 주입)
CMD ["python", "bot.py"]

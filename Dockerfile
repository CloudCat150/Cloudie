# Python 3.11 기반 슬림 이미지
FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libopus0 \
    libopus-dev \
    ffmpeg \
    lsof \
    && rm -rf /var/lib/apt/lists/*

# libopus.so 링크 생성 (discord.opus.load_opus('libopus.so') 호출 시 찾을 수 있도록)
RUN ln -s /usr/lib/x86_64-linux-gnu/libopus.so.0 /usr/lib/libopus.so

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

find / -name "libopus.so*"

# 봇 코드 복사
COPY . .

# libopus.so를 올바로 찾도록 LD_LIBRARY_PATH 설정
ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib

ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libopus.so.0

# 컨테이너 시작 시 봇 실행 (DISCORD_TOKEN은 외부에서 환경변수로 주입)
CMD ["python", "bot.py"]

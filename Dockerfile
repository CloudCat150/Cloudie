FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libopus0 \
    libopus-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# libopus.so 심볼릭 링크 생성
RUN find / -name "libopus.so*" && \
    ln -s $(find / -name "libopus.so.0" | head -n 1) /usr/lib/libopus.so || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib

CMD ["python", "run.py"]

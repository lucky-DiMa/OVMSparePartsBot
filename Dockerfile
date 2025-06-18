FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends  \
    build-essential libffi-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]

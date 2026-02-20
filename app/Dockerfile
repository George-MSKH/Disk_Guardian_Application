FROM python:3.11-slim

WORKDIR /app

# Install build tools required for psutil
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY guardian.py .

CMD [ "python", "-u", "guardian.py" ]
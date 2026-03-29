FROM python:3.11-slim

WORKDIR /app/services/device_manager

RUN apt-get update && apt-get install -y --no-install-recommends 
    gcc 
    && rm -rf /var/lib/apt/lists/*

COPY services/device_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/device_manager/ .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["python", "main.py"]
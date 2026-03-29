FROM python:3.8

# Set the working directory
WORKDIR /app

# Copy dependencies and application code
COPY services/device_manager/requirements.txt .
COPY services/device_manager/ .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start command
CMD ["python", "app.py"]
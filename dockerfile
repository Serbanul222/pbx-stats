# Use a slim Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Copy the entire project
COPY . .

# Expose the port Render uses
EXPOSE 8080

# Use gunicorn to run the application
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
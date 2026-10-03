FROM python:3.11-slim

# Prevent Python from writing bytecode and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install tzdata package via Debian package manager (apt-get) for reliable ZoneInfo support
# Keep image minimal by disabling recommended packages and cleaning package cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose API port
EXPOSE 8000

# Run FastAPI production server via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

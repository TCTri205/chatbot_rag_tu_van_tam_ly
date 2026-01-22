FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
# Increase timeout and split installation to avoid memory/network issues
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application code
COPY ./src ./src
COPY ./migrations ./migrations
COPY alembic.ini .

# Set PYTHONPATH so Python can find the 'src' module
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start server (migrations will be run manually after first setup)
CMD uvicorn src.main:app --host 0.0.0.0 --port 8000

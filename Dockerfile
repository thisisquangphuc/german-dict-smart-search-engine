FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Create data and resource directories with proper permissions
RUN mkdir -p /app/data /app/resource && chown -R appuser:appuser /app/data /app/resource

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary application files
COPY app/ /app/app/
COPY resource/ /app/resource/

# Set proper permissions
RUN chown -R appuser:appuser /app

# Set environment variables
ENV QUIZ_DATA_PATH=/app/data
ENV RESOURCE_PATH=/app/resource

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

LABEL org.opencontainers.image.source="https://github.com/thisisquangphuc/german-dict-smart-search-engine"
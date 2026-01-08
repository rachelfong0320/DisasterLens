# Stage 1: Build stage
FROM python:3.9-slim as builder

# Install build tools only for compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Copy only the installed packages from the builder
COPY --from=builder /root/.local /root/.local
# Copy the rest of the application code
COPY . .

# Ensure scripts in .local/bin are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Production command: Remove --reload for better performance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
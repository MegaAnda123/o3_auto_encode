# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-venv \
    git \
    ca-certificates \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
    && poetry --version

# Set the working directory inside the container
WORKDIR /app

# Copy pyproject.toml and poetry.lock to set up dependencies layer
COPY pyproject.toml poetry.lock ./

# Install dependencies without creating a virtual environment
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Ensure the app directory is in PYTHONPATH to resolve absolute imports
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "o3_auto_encode/main.py", "-c", "config.yaml", "-j", "/out/db.json"]

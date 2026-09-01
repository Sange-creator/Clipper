FROM python:3.11-slim

# Install system dependencies (FFmpeg, OpenCV essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system -r <(python -c 'import tomllib; f=open("pyproject.toml","rb"); data=tomllib.load(f); print("\n".join(data["project"]["dependencies"]))')

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

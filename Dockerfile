FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Run as non-root user (required for Hugging Face Spaces)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Install system dependencies (ffmpeg, libsndfile, and local redis-server)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=user:user . .

# Startup script launches local Redis and then the bot process.
COPY --chown=user:user docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

# Switch to the non-root user
USER user

# Expose the HF Spaces required port
EXPOSE 7860

# Command to run redis + bot
CMD ["/app/docker/entrypoint.sh"]

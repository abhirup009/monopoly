FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 3000

# Run the service
CMD ["python", "-m", "uvicorn", "src.main:socket_app", "--host", "0.0.0.0", "--port", "3000"]

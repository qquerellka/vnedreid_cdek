# Dockerfile
# #############################################################################
#
# Build image:
# >> docker build -t hh-api .
#
# Run container:
# >> docker run --rm --name my-app -it -p 3333:3333 hh-api
#
# #############################################################################

FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p data cache

# Run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

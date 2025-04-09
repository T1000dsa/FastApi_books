FROM python:latest

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# First copy only requirements to cache pip install
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Then copy the rest
COPY . .

# Ensure the .env file is explicitly copied
COPY .env .env

EXPOSE 8000

# Add this to verify environment variables
RUN echo "Environment variables in container:" && \
    printenv
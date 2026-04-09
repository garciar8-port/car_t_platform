FROM python:3.11-slim

WORKDIR /app

# System deps for building native extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install scheduler as editable package
COPY services/scheduler/ /app/services/scheduler/
RUN pip install --no-cache-dir -e /app/services/scheduler

# Install API requirements
COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy API source
COPY services/api/ /app/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim
WORKDIR /runner
COPY app.py .
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ default-jdk nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir fastapi uvicorn google-cloud-storage
USER 65532:65532
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

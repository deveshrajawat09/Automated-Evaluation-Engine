FROM python:3.12-slim
WORKDIR /runner
COPY app.py .
RUN pip install --no-cache-dir fastapi uvicorn
USER 65532:65532
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

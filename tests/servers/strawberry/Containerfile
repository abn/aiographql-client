FROM docker.io/python:3.14-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir .

ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000/tcp

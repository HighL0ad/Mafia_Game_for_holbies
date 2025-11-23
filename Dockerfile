FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main


EXPOSE 8000

CMD ["gunicorn", "-k", "gevent", "-w", "1", "--bind", "0.0.0.0:8000", "app:app"]
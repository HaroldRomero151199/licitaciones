FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# deps mínimas
RUN apt-get update && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

# install poetry
RUN pip install --no-cache-dir poetry==1.8.3

# copy deps first (cache)
COPY pyproject.toml poetry.lock* /app/

# install deps without venv
RUN poetry config virtualenvs.create false \
  && poetry install --only main --no-interaction --no-ansi

# copy app
COPY . /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

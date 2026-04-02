FROM python:3.12-slim

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY --chown=appuser:appuser pyproject.toml .
RUN pip install -e .

COPY --chown=appuser:appuser . .

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

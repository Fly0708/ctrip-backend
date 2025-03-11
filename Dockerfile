FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
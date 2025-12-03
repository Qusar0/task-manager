FROM python:3.11-slim

WORKDIR /app

COPY requirements.prod.txt /app/requirements.prod.txt
RUN pip install --no-cache-dir -r /app/requirements.prod.txt

COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11.9-slim

WORKDIR /app

ENV PIP_PREFER_BINARY=1

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.9-slim

RUN pip install flask

WORKDIR /app

COPY web_honeypot.py .

EXPOSE 80

CMD ["python", "web_honeypot.py"]
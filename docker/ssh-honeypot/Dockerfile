FROM python:3.9-slim

RUN pip install paramiko

WORKDIR /app

COPY ssh_honeypot.py .

EXPOSE 2222

CMD ["python", "ssh_honeypot.py"]
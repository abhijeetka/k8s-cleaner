FROM python:3.7-slim

ENV POD_STATUS=Running,Failed
ENV EXCLUDE_NAMESPACES=default,space
ENV EXPIRY_DAYS=1

ENV PYTHONUNBUFFERED=0

WORKDIR /app
COPY requirements.txt ./
COPY main.py ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
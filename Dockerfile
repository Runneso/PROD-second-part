FROM python:3.12.1-alpine3.19

WORKDIR /api

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .



CMD ["python", "main.py"]

FROM python:3.10-slim

WORKDIR /app

ENV PATH="/my/custom/path:${PATH}"

COPY main.py .

COPY requirements.txt .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]

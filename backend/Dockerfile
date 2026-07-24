from python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static/uploads

ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "run.py"]

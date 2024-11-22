FROM python:3.13-slim
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app
COPY main.py /app
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
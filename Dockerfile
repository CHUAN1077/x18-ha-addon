FROM python:3.11-slim

WORKDIR /app
RUN pip install flask python-osc

COPY x18_bridge.py /app/x18_bridge.py

CMD ["python3", "/app/x18_bridge.py"]
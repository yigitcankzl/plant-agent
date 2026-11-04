# Replay-only PlantAgent: the stored runs, no API key, no engineering engines.
#   docker build -t plantagent . && docker run --rm -p 127.0.0.1:8765:8765 plantagent
#   then open http://localhost:8765/home.html
# The app keeps its own rule (it only answers on localhost without a token), so it listens on 127.0.0.1 inside the
# container and socat forwards the published port to it. Live Muse calls and re-solving need ./start.sh --live and
# the engines on the host (docs/running.md).
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends socat && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV WEB_ALLOW_RUNS=0
EXPOSE 8765
CMD ["sh", "-c", "python -m plantagent.web --port 8766 & exec socat TCP-LISTEN:8765,fork,reuseaddr TCP:127.0.0.1:8766"]

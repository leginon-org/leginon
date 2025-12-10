FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo/docs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN git config --global --add safe.directory /repo

# Note: repo will be mounted at /repo at runtime
# This allows live editing without rebuilding the image

EXPOSE 8000

CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]

# Build context: repo root (needs src/agent_govbench for the synthetic world).
FROM python:3.12-slim
RUN pip install --no-cache-dir "fastmcp>=3.2.0,<4" "uvicorn>=0.34" "starlette>=0.41" "google-cloud-storage>=2.18"
RUN groupadd -g 65532 nonroot && useradd -u 65532 -g 65532 -s /bin/false nonroot
WORKDIR /app
COPY src/agent_govbench/__init__.py src/agent_govbench/policy.py src/agent_govbench/world.py /app/agent_govbench/
COPY services/tools/main.py /app/main.py
USER 65532:65532
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

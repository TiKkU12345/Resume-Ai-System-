# # Resume Shortlisting System - Production Dockerfile
# # Multi-stage build for optimal image size

# # Stage 1: Builder
# FROM python:3.11-slim as builder

# WORKDIR /app

# # Install build dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     gcc \
#     g++ \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir --user -r requirements.txt

# # Install spaCy model in builder stage
# RUN pip install --no-cache-dir --user https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# # Stage 2: Runtime
# FROM python:3.11-slim

# WORKDIR /app

# # Install runtime dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgomp1 \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Copy installed packages from builder (includes spaCy model)
# COPY --from=builder /root/.local /root/.local

# # Make scripts usable
# ENV PATH=/root/.local/bin:$PATH

# # Copy application code
# COPY . .

# # Create directories
# RUN mkdir -p /app/temp /app/uploads /app/data

# # Expose Streamlit port
# EXPOSE 8501

# # Health check
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8501/_stcore/health || exit 1

# # Streamlit config
# ENV STREAMLIT_SERVER_PORT=8501 \
#     STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
#     STREAMLIT_SERVER_HEADLESS=true \
#     STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# # Run app
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
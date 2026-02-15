# syntax=docker/dockerfile:1
FROM python:3.13-slim

# Build variant: 'cpu' (default) or 'cuda'
ARG VARIANT=cpu

# Install system dependencies first
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .

# Install PyTorch family: CPU uses explicit index, CUDA uses default/latest
RUN TORCH_INDEX="" && \
    if [ "${VARIANT}" = "cpu" ]; then \
        TORCH_INDEX="--index-url https://download.pytorch.org/whl/cpu"; \
        echo ">>> Installing CPU-optimized PyTorch"; \
    else \
        echo ">>> Installing default/latest CUDA PyTorch"; \
    fi && \
    pip install --no-cache-dir torch torchaudio ${TORCH_INDEX}

# Install remaining dependencies + correct ONNX variant
RUN ONNX_PKG="onnxruntime" && \
    if [ "${VARIANT}" != "cpu" ]; then \
        ONNX_PKG="onnxruntime-gpu"; \
        echo ">>> Installing GPU-optimized ONNX Runtime"; \
    else \
        echo ">>> Installing CPU ONNX Runtime"; \
    fi && \
    pip install --no-cache-dir -r requirements.txt ${ONNX_PKG}

# Copy application
COPY . .
COPY cfg/docker.cfg default.cfg

# Optional: runtime metadata for introspection
ENV EBOOKTALKER_VARIANT=${VARIANT}
LABEL org.ebooktalker.variant=${VARIANT}

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
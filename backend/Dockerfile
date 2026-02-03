# ==========================================
# Stage 1: Builder (Compile AI dependencies)
# ==========================================
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CMAKE_ARGS="-DGGML_CUDA=on" \
    FORCE_CMAKE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Warsaw

WORKDIR /app

# Install build dependencies (single RUN for layer efficiency)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        git \
        build-essential \
        cmake \
        curl \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.13 \
        python3.13-venv \
        python3.13-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create virtual environment
ENV UV_PYTHON=python3.13
RUN uv venv /app/.venv

# Install dependencies into the virtual environment
# IMPORTANT: llama-cpp-python needs libcuda.so.1 for linking, but in devel image
# it's only a stub at /usr/local/cuda/lib64/stubs/libcuda.so
# We must add stubs to LD_LIBRARY_PATH and create symlink for the linker
COPY pyproject.toml uv.lock ./
RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 && \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:$LD_LIBRARY_PATH \
    uv sync --frozen --no-install-project && \
    # Aggressive cleanup to reduce image size (~2-3 GB savings)
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyo" -delete 2>/dev/null || true && \
    find /app/.venv -type f -name "*.md" -delete 2>/dev/null || true && \
    find /app/.venv -type f -name "*.txt" ! -name "requirements*.txt" -delete 2>/dev/null || true && \
    # Remove triton (540MB) - only needed for torch.compile which we don't use
    rm -rf /app/.venv/lib/python3.13/site-packages/triton 2>/dev/null || true
    # NOTE: Keep ALL nvidia/* libs - removing them causes ImportError at runtime
    # PyTorch bundles specific versions that may differ from base image

# ==========================================
# Stage 2: Runtime (Slim production image)
# ==========================================
# Use cudnn-runtime for cuDNN support (required for inference)
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Warsaw

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.13 \
        libgomp1 \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# NOTE: Healthcheck defined in docker-compose.yml only (avoid redundancy)

# Production: Single worker for GPU workloads to avoid VRAM issues
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]


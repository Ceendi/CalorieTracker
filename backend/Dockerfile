# ==========================================
# Stage 1: Builder (Compile AI dependencies)
# ==========================================
# NOTE: Upgrade to ubuntu24.04 when moving to CUDA 12.6+
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

# Build-only arg — not persisted in the final image
ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CMAKE_ARGS="-DGGML_CUDA=on" \
    FORCE_CMAKE=1

WORKDIR /app

# Install build dependencies (single RUN for layer efficiency)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.13 \
        python3.13-venv \
        python3.13-dev \
        build-essential \
        cmake \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv — pin to a specific version for reproducible builds
# Verify latest stable at: https://github.com/astral-sh/uv/releases
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# Create virtual environment
ENV UV_PYTHON=python3.13
RUN uv venv /app/.venv

# Install dependencies into the virtual environment
# llama-cpp-python needs libcuda.so.1 for linking; in devel image
# it's only a stub at /usr/local/cuda/lib64/stubs/libcuda.so
COPY pyproject.toml uv.lock ./
RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1 && \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs:$LD_LIBRARY_PATH \
    uv sync --frozen --no-install-project && \
    # Cleanup to reduce image size (~2-3 GB savings) \
    # IMPORTANT: Never delete files inside .dist-info — breaks importlib.metadata \
    find /app/.venv -type d -name "tests" -not -path "*.dist-info*" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "test" -not -path "*.dist-info*" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "docs" -not -path "*.dist-info*" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.pyo" -delete 2>/dev/null || true && \
    # Remove triton (~540MB) — only needed for torch.compile which we don't use \
    find /app/.venv -type d -name "triton" -path "*/site-packages/*" -exec rm -rf {} + 2>/dev/null || true
    # NOTE: Keep ALL nvidia/* libs — removing them causes ImportError at runtime
    # NOTE: .pyc files are kept — UV_COMPILE_BYTECODE=1 pre-compiles them for faster startup

# ==========================================
# Stage 2: Runtime (Slim production image)
# ==========================================
# cudnn-runtime provides cuDNN support required for PyTorch/Whisper inference
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS runtime

# Build-only arg — not persisted in the final image
ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    TZ=UTC

WORKDIR /app

# Create non-root user before COPY to use --chown (avoids expensive chown -R layer)
RUN useradd -m -u 1000 appuser

# Install only runtime dependencies, then remove PPA tooling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.13 \
        libgomp1 \
        curl \
        ffmpeg \
    && apt-get purge -y --auto-remove software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage (with correct ownership)
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Healthcheck defined in docker-compose.yml only (avoid redundancy)

# Production: single worker for GPU workloads to avoid VRAM contention
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-graceful-shutdown", "30"]

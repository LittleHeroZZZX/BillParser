FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps)
RUN uv sync --frozen --no-dev

# Copy source code and config
COPY billparser/ ./billparser/
COPY config/ ./config/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8878

CMD ["python", "-m", "billparser.cli", "serve"]

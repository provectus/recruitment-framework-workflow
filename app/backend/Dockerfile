# Base stage with uv and dependencies
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .
RUN chmod +x entrypoint.sh

# Development stage
FROM base AS dev
RUN uv sync --frozen
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]

# Production stage
FROM base AS prod
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0"]

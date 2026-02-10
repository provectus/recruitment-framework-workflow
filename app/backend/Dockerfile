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

# Development stage
FROM base AS dev

# Install dev dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run development server with hot reload
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]

# Production stage
FROM base AS prod

# Expose port
EXPOSE 8000

# Run production server
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0"]

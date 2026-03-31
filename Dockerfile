# Start with a minimal Python image
FROM python:3.13-slim-bookworm

# Copy the uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster app startup
ENV UV_COMPILE_BYTECODE=1

# Copy only the lockfile and pyproject.toml first (for Docker caching)
COPY uv.lock pyproject.toml /app/

# Install production dependencies ONLY (no dev tools) into the system Python
RUN uv sync --frozen --no-dev --no-install-project

# Copy your actual FastAPI/HTMX application code (main.py, templates, etc.)
COPY . /app

# Install the project itself
RUN uv sync --frozen --no-dev

# Put the uv-managed virtual environment on the system PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run the FastAPI server
# (Assuming your app is in main.py and the instance is called 'app')
CMD ["fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]
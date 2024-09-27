FROM python:3.11-slim
WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip && \
    pip install poetry

# Copy only the necessary files for dependency installation
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .
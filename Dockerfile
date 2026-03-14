FROM python:3.11-slim
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements file for dependency installation
COPY requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .
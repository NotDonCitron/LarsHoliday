# Use a specialized Playwright/Patchright compatible base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y 
    wget 
    gnupg 
    libnss3 
    libnspr4 
    libatk1.0-0 
    libatk-bridge2.0-0 
    libcups2 
    libdrm2 
    libxkbcommon0 
    libxcomposite1 
    libxdamage1 
    libxext6 
    libxfixes3 
    libxrandr2 
    libgbm1 
    libasound2 
    && rm -rf /var/lib/apt/lists/*

# Create and switch to a non-root user
RUN useradd -m -u 1000 user
USER user
WORKDIR $HOME/app

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install patchright browsers
RUN python3 -m patchright install chromium

# Copy the rest of the application
COPY --chown=user . .

# Expose Hugging Face standard port
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "api.py", "--host", "0.0.0.0", "--port", "7860"]
